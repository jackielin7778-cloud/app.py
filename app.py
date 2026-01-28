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
    if os.path.exists("rules.csv"):
        rules_df = pd.read_csv("rules.csv")
        context += "【1. API 業務規範細則】:\n" + rules_df.to_string(index=False) + "\n\n"
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【2. 公司標準錯誤碼對照表】:\n" + errors_df.to_string(index=False) + "\n"
    return context

# ==========================================
# 2. 介面設定 (移除模型選單)
# ==========================================
st.set_page_config(page_title="AI API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    # 僅保留語系選擇，將複雜的模型邏輯隱藏在後台
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 執行分析", "dl": "📂 下載報告"},
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

genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))

# ==========================================
# 4. 主介面：全自動分析邏輯
# ==========================================
st.title(T["header"])

col1, col2 = st.columns(2)

with col1:
    user_input = st.text_area("待測 JSON 資料:", height=450, placeholder='請在此處貼上 JSON...')
    analyze_btn = st.button(T["btn"])

with col2:
    if analyze_btn and user_input:
        context_data = load_context_data()
        
        # --- 自動跳轉邏輯 (Auto-Routing) ---
        # 定義優先順序：Gemini 3 (最新) -> 2.0 Flash (主流) -> 1.5 Flash (穩定備援)
        priority_models = [
            "gemini-3-flash-preview", 
            "gemini-2.0-flash", 
            "gemini-1.5-flash"
        ]
        
        final_result = ""
        success_model = ""

        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"{context_data}\n\n待測資料：\n{user_input}\n\n任務：指出錯誤並標註 [ErrorCode]，使用 {lang_choice}。"
                
                with st.spinner(f"AI 正在進行深度診斷..."):
                    response = model.generate_content(prompt)
                    final_result = response.text
                    success_model = m_name # 記錄成功運算的模型
                break # 成功即跳出循環
            except Exception:
                # 若當前模型報錯（如 429 額度滿），靜默跳轉至下一個，不干擾 User
                continue
        
        if final_result:
            # 在結果上方給予小提示，讓 User 知道後台發生了什麼（選選）
            st.caption(f"💡 診斷完成 (後台已自動切換至優化路徑: {success_model})")
            st.session_state['report'] = final_result
            st.markdown(final_result)
            st.divider()
            st.download_button(T["dl"], data=final_result, file_name="Report.txt")
        else:
            st.error("目前所有 AI 引擎皆忙碌中，請稍後再試。")
