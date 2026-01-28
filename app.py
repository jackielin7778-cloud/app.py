import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：讀取專屬規格
# ==========================================
def load_api_spec(api_code):
    context = ""
    file_name = f"rules_{api_code}.csv"
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【{api_code} 專屬規範】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 檔案 {file_name} 讀取失敗。\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【通用錯誤碼】\n" + errors_df.to_string(index=False) + "\n"
        except:
            pass
    return context

# ==========================================
# 2. 介面初始化
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系", ["繁體中文", "English"])
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 執行分析", "dl": "📂 下載報告"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report"}
    }[lang_choice]
    
    if st.button("Logout"):
        st.session_state['auth'] = False
        st.rerun()

# ==========================================
# 3. 權限驗證
# ==========================================
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    pwd = st.text_input("Access Code:", type="password")
    if st.button("Login"):
        if pwd == "TEST2026": 
            st.session_state['auth'] = True
            st.rerun()
    st.stop()

# 安全配置 API Key
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("❌ 無法載入 API Key，請檢查 Streamlit Secrets 設定。")
    st.stop()

# ==========================================
# 4. 主介面：智慧連動三層選單
# ==========================================
st.title(T["header"])

# 定義層級邏輯資料庫
# 結構：大類 -> 體系 -> 子系列清單
api_tree = {
    "發票類 (Invoice)": {
        "format": "XML",
        "series": {
            "C系列": ["C0401", "C0501", "C0701", "D0401", "D0501"],
            "F系列": ["F0401", "F0501", "F0701", "G0401", "G0501"]
        }
    },
    "訂單類 (Order)": {
        "format": "JSON",
        "series": {
            "C系列": ["C0403", "C0503", "C0703", "D0403", "D0503"],
            "F系列": ["F0403", "F0503", "F0703", "G0403", "G0503"]
        }
    }
}

st.subheader("📍 步驟一：設定診斷路徑")
c1, c2, c3 = st.columns(3)

with c1:
    # 1. 選擇「發票」或「訂單」
    selected_main = st.selectbox("1. 選擇業務大類：", list(api_tree.keys()))
    expected_format = api_tree[selected_main]["format"]

with c2:
    # 2. 選擇「C系列」或「F系列」
    selected_series_name = st.selectbox("2. 選擇體系：", list(api_tree[selected_main]["series"].keys()))

with c3:
    # 3. 選擇子系列 (僅出現對應的代號)
    sub_list = api_tree[selected_main]["series"][selected_series_name]
    selected_code = st.selectbox("3. 選擇 API 代號：", sub_list)

# 自動提示目前的格式鎖定狀態
st.success(f"已鎖定體系：**{selected_code}** | 格式要求：**{expected_format}**")
st.divider()

# ==========================================
# 5. 輸入與 AI 分析
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.write(f"### 步驟二：貼入 {expected_format} 資料")
    user_input = st.text_area("Payload Input:", height=450, placeholder=f"請在此貼入 {selected_code} 的內容...")
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.write("### 步驟三：AI 診斷報告")
    if analyze_btn and user_input:
        spec_context = load_api_spec(selected_code)
        # 模型跳轉路徑
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        used_model = ""

        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家。現在要診斷的是 {selected_main} 中的 {selected_code}。
                此業務必須符合 {expected_format} 格式。
                
                規則規範：
                {spec_context}
                
                待測資料：
                {user_input}
                
                任務：
                1. 檢查資料是否符合規則。
                2. 若有不符，指出錯誤點並標註對應的 [ErrorCode]。
                3. 使用 {lang_choice} 給出建議與修正範例。
                """
                with st.spinner(f"正在透過 {m_name} 分析中..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                    used_model = m_name
                break 
            except:
                continue

        if final_report:
            st.caption(f"💡 引擎狀態：{used_model} 運算完成")
            st.markdown(final_report)
            st.divider()
            st.download_button(T["dl"], data=final_report, file_name=f"Report_{selected_code}.txt")
