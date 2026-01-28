import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：讀取 CSV 數據
# ==========================================
def load_context_data():
    context = ""
    # 讀取規則表
    if os.path.exists("rules.csv"):
        rules_df = pd.read_csv("rules.csv")
        context += "【1. API 業務規範細則】:\n" + rules_df.to_string(index=False) + "\n\n"
    # 讀取錯誤碼表
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【2. 公司標準錯誤碼對照表】:\n" + errors_df.to_string(index=False) + "\n"
    return context

# ==========================================
# 2. 介面選單配置
# ==========================================
st.set_page_config(page_title="AI API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    
    # --- 模型選單清單 (包含 Gemini 3) ---
    model_list = [
        "gemini-3-flash-preview",  # 最新預覽版
        "gemini-2.0-flash-lite", 
        "gemini-2.0-flash", 
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    model_choice = st.selectbox(
        "🧠 選擇 AI 大腦 (Model)",
        model_list,
        help="Gemini 3 Flash Preview 是目前最新的高效能模型。"
    )
    
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 執行分析", "dl": "📂 下載 TXT 報告"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report"}
    }[lang_choice]

# ==========================================
# 3. 權限驗證 (邀請碼)
# ==========================================
ACCESS_CODE = "TEST2026"
if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    pwd = st.text_input("Access Code:", type="password")
    if st.button("Login"):
        if pwd == ACCESS_CODE: 
            st.session_state['auth'] = True
            st.rerun()
    st.stop()

# 載入 API KEY (請確保 Streamlit Cloud Secrets 已設定)
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))

# ==========================================
# 4. 主介面：診斷邏輯
# ==========================================
st.title(T["header"])
st.info(f"當前模式：使用 **{model_choice}** 進行深度診斷")

col1, col2 = st.columns(2)

with col1:
    user_input = st.text_area("待測 JSON 資料:", height=450, placeholder='請在此處貼上 JSON...')
    analyze_btn = st.button(T["btn"])

with col2:
    if analyze_btn and user_input:
        context_data = load_context_data()
        
        # 建立自動備援清單：優先用選定的，失敗則往後遞補
        fallback_models = [model_choice, "gemini-1.5-flash"]
        models_to_try = list(dict.fromkeys(fallback_models))
        
        final_result = ""
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                # 強化 Prompt
                prompt = f"""
                系統規範：
                {context_data}
                
                分析對象：
                {user_input}
                
                任務：
                1. 請檢查資料是否符合業務規範細則。
                2. 若有錯誤，必須對應錯誤碼表並標註 [ErrorCode]。
                3. 請使用 {lang_choice} 給出診斷結論與修正後的範例。
                """
                
                with st.spinner(f"正在透過 {m_name} 運算中..."):
                    response = model.generate_content(prompt)
                    final_result = response.text
                break 
            except Exception as e:
                st.warning(f"模型 {m_name} 暫時無法回應，正在嘗試備援...")
                continue
        
        if final_result:
            st.session_
