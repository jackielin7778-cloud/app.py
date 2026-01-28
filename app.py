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
# 2. 介面選單配置
# ==========================================
st.set_page_config(page_title="AI API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("🛡️ 系統控制面板")
    
    # 使用 st.expander 將「非核心選單」隱藏起來
    with st.expander("⚙️ 進階模型與語系設定", expanded=False):
        lang_choice = st.selectbox("🌐 選擇語系 (Language)", ["繁體中文", "English"])
        
        model_list = [
            "gemini-3-flash-preview", 
            "gemini-2.0-flash-lite", 
            "gemini-2.0-flash", 
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        model_choice = st.selectbox("🧠 選擇 AI 模型", model_list, index=0)
        st.caption("提示：若預覽版模型不穩定，請手動切換至 1.5-flash。")

    # 定義多語系文字標籤
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
    pwd = st.text_input("請輸入訪問代碼 (Access Code):", type="password")
    if st.button("登入系統"):
        if pwd == ACCESS_CODE: 
            st.session_state['auth'] = True
            st.rerun()
    st.stop()

# 載入 API KEY
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))

# ==========================================
# 4. 主介面：診斷邏輯
# =================================
