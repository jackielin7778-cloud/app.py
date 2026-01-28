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
    # 建立對應的檔案名稱 (rules_C.csv 或 rules_F.csv)
    file_name = f"rules_{api_series}.csv"
    
    # 載入業務規則
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【重要：當前參考 {api_series} 系列業務規範】\n{df.to_string(index=False)}\n\n"
        except Exception as e:
            context += f"⚠️ 無法讀取 {file_name}，請檢查檔案格式。\n\n"
    else:
        context += f"⚠️ 系統找不到 {file_name}，將採用通用邏輯進行分析。\n\n"
    
    # 載入通用錯誤碼
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

# 側邊欄：系統選單
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
# 3. 登入權限驗證
# ==========================================
ACCESS_CODE = "TEST2026"
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🛡️ Secure Login")
    pwd = st.text_input("請輸入邀請碼 (Access Code):", type="password")
    if st.button("登入"):
        if pwd == ACCESS_CODE:
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("代碼錯誤，請洽管理員。")
    st.stop()

# 配置 Google AI (從 Secrets 取得 API Key)
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰。請在 Streamlit 控制台設定 GEMINI_API_KEY。")
    st.stop()
genai.configure(api_key=st.secrets["GEM
