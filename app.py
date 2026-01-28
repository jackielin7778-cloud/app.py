import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：動態讀取規則與錯誤碼
# ==========================================
def load_spec_data(api_series):
    context = ""
    # 建立對應的檔案名稱 (如 rules_C.csv)
    file_name = f"rules_{api_series}.csv"
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【重要：當前參考 {api_series} 系列業務規範】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 無法讀取 {file_name}，請檢查檔案格式。\n\n"
    else:
        context += f"⚠️ 系統找不到 {file_name}，將採用一般邏輯進行分析。\n\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：公司標準錯誤碼對照表】\n" + errors_df.to_string(index=False) + "\n"
        except:
            pass
            
    return context

# ==========================================
# 2. 頁面初始化與語系設定
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    
    T = {
        "繁體中文": {
            "header": "🛡️ API 自動化診斷系統",
            "select_title": "第一步：選擇 API 檢查體系",
            "input_title": "第二步：貼入待測資料 (JSON)",
            "output_title": "第三步：AI 診斷結果",
            "btn": "🚀 開始執行分析",
            "dl": "📂 下載分析報告"
        },
        "English": {
            "header": "🛡️ API Automated Validator",
            "select_title": "Step 1: Select API Series",
            "input_title": "Step 2: Paste JSON Data",
            "output_title": "Step 3: AI Diagnosis",
            "btn": "🚀 Run Analysis",
            "dl": "📂 Download Report"
        }
    }[lang_choice]
    
    st.divider()
    if st.button("Logout / 登出"):
        st.session_state['auth'] = False
        st.rerun()

# ==========================================
# 3. 權限驗證
# ==========================================
ACCESS_CODE = "TEST2026"
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🛡️ Secure Access")
    pwd = st.text_input("請輸入邀請碼:", type="password")
    if st.button("登入"):
        if pwd == ACCESS_CODE:
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("邀請碼錯誤")
    st.stop()

# ⚠️ 這裡最容易出錯，請確保整行完整
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("❌ Secrets 中找不到 GEMINI_API_KEY，請檢查 Streamlit Cloud 設定。")
    st.stop()

# ==========================================
# 4. 主介面：體系選擇與輸入
# ==========================================
st.title(T["header"])

st.subheader(T["select_title"])
api_option = st.selectbox(
    "請確認目前要檢查的業務範圍：",
    [
        "C系列 (包含：C0403, C0503, C0703, D0403, D0503)",
        "F系列 (包含：F0403, F0503, F0703, G0403, G0503)"
    ]
)
current_series = "C" if "C系列" in api_option else "F"

st.divider()

col_in, col_out = st.columns(2)

with col_in:
    st.subheader(f"{T['input_title']} ({current_series})")
    user_input = st.text_area("JSON Payload:", height=450, placeholder='{"Main": {...}}')
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.subheader(T["output_title"])
    
    if analyze_btn and user_input:
        spec_context = load_spec_data(current_series)
        
        # ⚠️ 確保清單引號閉合
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        used_model = ""

        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家。請根據以下規範校對 JSON：
                {spec_context}
                
                使用者資料：
                {user_input}
                
                任務：
                1. 比對規範指出錯誤。
                2. 標註對應的 [ErrorCode]。
                3. 使用 {lang_choice} 提供修正建議。
                """
                with st.spinner(f"正在透過 {m_name} 進行分析..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                    used_model = m_name
                break 
            except:
                continue

        if final_report:
            st.caption(f"✅ 引擎：{used_model}")
            st.markdown(final_report)
            st.divider()
            st.download_button(
                label=T["dl"],
                data=final_report,
                file_name=f"Report_{current_series}.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ 所有模型均暫時無法連線。")
