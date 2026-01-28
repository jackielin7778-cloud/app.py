import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：讀取專屬規格檔
# ==========================================
def load_api_spec(api_code):
    context = ""
    file_name = f"rules_{api_code}.csv"
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【當前代號：{api_code} 專屬規範】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 檔案 {file_name} 讀取失敗。\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：通用錯誤碼對照表】\n" + errors_df.to_string(index=False) + "\n"
        except:
            pass
    return context

# ==========================================
# 2. 頁面初始化
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 執行分析", "dl": "📂 下載報告"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report"}
    }[lang_choice]
    
    if st.button("Logout / 登出"):
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

# 安全載入 API Key
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("❌ 無法載入 API Key")
    st.stop()

# ==========================================
# 4. 主介面：兩層式點選選單
# ==========================================
st.title(T["header"])

# 定義層級資料
api_hierarchy = {
    "C系列 (體系一)": {
        "JSON (訂單類)": ["C0403", "C0503", "C0703", "D0403", "D0503"],
        "XML (發票類)": ["C0401", "C0501", "C0701", "D0401", "D0501"]
    },
    "F系列 (體系二)": {
        "JSON (訂單類)": ["F0403", "F0503", "F0703", "G0403", "G0503"],
        "XML (發票類)": ["F0401", "F0501", "F0701", "G0401", "G0501"]
    }
}

st.subheader("第一步：設定診斷標的")
col_sel1, col_sel2, col_sel3 = st.columns(3)

with col_sel1:
    main_series = st.selectbox("1. 選擇主系列：", list(api_hierarchy.keys()))

with col_sel2:
    sub_categories = list(api_hierarchy[main_series].keys())
    sub_category = st.selectbox("2. 選擇資料類別：", sub_categories)

with col_sel3:
    # 第三層：改為點選式下拉選單 (也可改為 st.radio 如果選項不多)
    final_code_list = api_hierarchy[main_series][sub_category]
    selected_code = st.selectbox("3. 選擇具體代號：", final_code_list)

# 自動判定格式
expected_format = "JSON" if "JSON" in sub_category else "XML"

st.success(f"📍 準備就緒：**{selected_code}** ({expected_format})")
st.divider()

# ==========================================
# 5. 輸入與 AI 分析區
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.write(f"### 第二步：貼入資料")
    user_input = st.text_area(f"請貼入 {selected_code} 的 {expected_format} 內容：", height=450)
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.write("### 第三步：AI 分析報告")
    if analyze_btn and user_input:
        spec_context = load_api_spec(selected_code)
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家。
                任務：檢查代號 {selected_code}，格式需符合 {expected_format}。
                
                規格參考：
                {spec_context}
                
                使用者資料：
                {user_input}
                
                請指出錯誤、標註 [ErrorCode] 並提供修正範例 (以 {lang_choice} 回覆)。
                """
                with st.spinner(f"正在透過 {m_name} 進行分析..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                break 
            except:
                continue

        if final_report:
            st.markdown(final_report)
            st.divider()
            st.download_button(T["dl"], data=final_report, file_name=f"Report_{selected_code}.txt")
