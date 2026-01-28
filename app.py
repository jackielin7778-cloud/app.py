import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：根據代號讀取專屬 CSV
# ==========================================
def load_api_spec(api_code):
    context = ""
    file_name = f"rules_{api_code}.csv"
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【針對 {api_code} 的專屬審核規範】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 檔案 {file_name} 讀取失敗。\n"
    else:
        context += f"⚠️ 找不到 {file_name}，將進行通用邏輯檢查。\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：通用錯誤碼】\n" + errors_df.to_string(index=False) + "\n"
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

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 4. 主介面：10 大代號獨立選擇
# ==========================================
st.title(T["header"])

# 定義 10 個代號及其屬性
api_configs = {
    "C0403": "JSON", "C0503": "JSON", "C0703": "JSON", "D0403": "JSON", "D0503": "JSON",
    "F0403": "JSON", "F0503": "JSON", "F0703": "JSON", "G0403": "JSON", "G0503": "JSON",
    "C0401": "XML",  "C0501": "XML",  "C0701": "XML",  "D0401": "XML",  "D0501": "XML",
    "F0401": "XML",  "F0501": "XML",  "F0701": "XML",  "G0401": "XML",  "G0501": "XML"
}

st.subheader("第一步：選擇 API 代號")
selected_code = st.selectbox("請選擇您要檢查的 API 代號：", list(api_configs.keys()))

expected_format = api_configs[selected_code]

st.info(f"✅ 已選定：**{selected_code}** | 系統將自動以 **{expected_format}** 格式規格進行校對。")
st.divider()

# ==========================================
# 5. 輸入與 AI 分析
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.write(f"### 第二步：貼入資料 ({expected_format})")
    user_input = st.text_area("Input Payload:", height=450)
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.write("### 第三步：診斷結果")
    if analyze_btn and user_input:
        spec_context = load_api_spec(selected_code)
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家。現在要檢查的代號是：{selected_code}。
                預期格式為：{expected_format}。
                請根據以下專屬規範校對：
                {spec_context}
                
                使用者資料：
                {user_input}
                
                要求：
                1. 嚴格核對欄位是否符合 {selected_code} 的規格。
                2. 發現錯誤請標註 [ErrorCode]。
                3. 使用 {lang_choice} 回覆結果與建議。
                """
                with st.spinner(f"正在透過 {m_name} 校對 {selected_code}..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                break 
            except:
                continue

        if final_report:
            st.markdown(final_report)
            st.divider()
            st.download_button(T["dl"], data=final_report, file_name=f"Report_{selected_code}.txt")
