import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：讀取 CSV
# ==========================================
def load_context_data():
    context = ""
    if os.path.exists("rules.csv"):
        rules_df = pd.read_csv("rules.csv")
        context += "【1. API 業務規範細則】:\n" + rules_df.to_string(index=False) + "\n\n"
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【2. 公司標準錯誤碼對照表】:\n" + errors_df.to_string(index=False) + "\n"
    return context

# ==========================================
# 2. 介面與模型選單設定
# ==========================================
st.set_page_config(page_title="AI API Validator", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 設定中心")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    
    # --- 新增：模型切換選單 ---
    # 讓 User 根據需求選擇模型
    model_choice = st.selectbox(
        "🧠 選擇 AI 模型 (Model)",
        [
            "gemini-2.0-flash-lite", 
            "gemini-2.0-flash", 
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ],
        help="Lite 最快且省額度；Pro 最聰明但速度慢且額度緊。"
    )
    
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 開始分析", "dl": "📂 下載報告"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report"}
    }[lang_choice]

# ==========================================
# 3. 權限與 API 設定
# ==========================================
ACCESS_CODE = "TEST2026"
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    pwd = st.text_input("輸入邀請碼 (Access Code):", type="password")
    if st.button("登入 (Login)"):
        if pwd == ACCESS_CODE: 
            st.session_state['auth'] = True
            st.rerun()
    st.stop()

genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))

# ==========================================
# 4. 主介面
# ==========================================
st.title(T["header"])
st.info(f"當前使用模型：**{model_choice}**")

col1, col2 = st.columns(2)

with col1:
    user_input = st.text_area("JSON Payload:", height=450)
    analyze_btn = st.button(T["btn"])

with col2:
    if analyze_btn and user_input:
        context_data = load_context_data()
        
        # 建立嘗試清單：優先用 User 選的模型，失敗則自動備援至 1.5-flash
        fallback_models = [model_choice, "gemini-1.5-flash"]
        # 去重，保持選定的模型在最前面
        models_to_try = list(dict.fromkeys(fallback_models))
        
        final_result = ""
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"{context_data}\n\n待測資料：\n{user_input}\n\n任務：請對照規則指出錯誤並標註 [ErrorCode]，使用 {lang_choice}。"
                
                with st.spinner(f"正在使用 {m_name} 分析中..."):
                    response = model.generate_content(prompt)
                    final_result = response.text
                break # 成功就跳出循環
            except Exception as e:
                st.warning(f"模型 {m_name} 暫時無法使用，嘗試切換至備援模型...")
                continue
        
        if final_result:
            st.session_state['report'] = final_result
            st.markdown(final_result)
            st.divider()
            st.download_button(T["dl"], data=final_result, file_name="report.txt")
        else:
            st.error("所有模型均無法回應，請檢查 API Key 或網路。")
