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
    selected_series_name = st.selectbox("2. 選擇體系：", list(api_tree[selected_main]["
