import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：動態讀取規格 CSV
# ==========================================
def load_spec_data(api_series):
    context = ""
    # 根據代號決定讀取 rules_C.csv 或 rules_F.csv
    file_name = f"rules_{api_series}.csv"
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        context += f"【重要：當前為 {api_series} 系列規格】\n{df.to_string(index=False)}\n\n"
    
    # 載入通用錯誤碼
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【參考：通用錯誤碼對照表】\n" + errors_df.to_string(index=False) + "\n"
        
    return context

# ==========================================
# 2. 介面與語系初始化
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

# 側邊欄僅保留語系與登出
with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 開始分析", "dl": "📂 下載報告", "select": "第一步：選擇 API 體系"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report", "select": "Step 1: Select API Series"}
    }[lang_choice]
    
    if st.button("Logout / 登出"):
        st.session_state['auth'] = False
        st.rerun()

# ==========================================
# 3. 權限驗證
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
# 4. 主介面：API 體系單獨選擇區
# ==========================================
st.title(T["header"])

# --- 單獨列出 API 體系選擇 ---
st.subheader(T["select"])
api_category = st.selectbox(
    "請點擊下拉選單切換體系：",
    [
        "C系列 (包含：C0403, C0503, C0703, D0403, D0503)",
        "F系列 (包含：F0403, F0503, F0703, G0403, G0503)"
    ]
)

# 內部代號轉換邏輯
current_series = "C" if "C系列" in api_category else "F"

st.divider()

# ==========================================
# 5. 分析與輸入區
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.write(f"### 第二步：貼入 {current_series} 系列 JSON")
    user_input = st.text_area("JSON Payload:", height=400, placeholder='{"Main": {"MessageId": "C0403", ...}}')
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col2:
    st.write("### 第三步：診斷結果")
    if analyze_btn and user_input:
        spec_context = load_spec_data(current_series)
        
        # 自動路由模型順序
        priority_models = ["gemini-3-flash-preview", "gemini
