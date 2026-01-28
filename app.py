import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：動態讀取規格
# ==========================================
def load_spec_data(category_key, series_key):
    context = ""
    # 檔案命名規則：rules_Order_C.csv / rules_Invoice_F.csv 等
    file_name = f"rules_{category_key}_{series_key}.csv"
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【重要規範：{category_key}類 - {series_key}系列】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 無法讀取 {file_name}，請檢查檔案。\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：通用錯誤碼】\n" + errors_df.to_string(index=False) + "\n"
        except:
            pass
    return context

# ==========================================
# 2. 介面與語系
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 Language", ["繁體中文", "English"])
    T = {
        "繁體中文": {
            "header": "🛡️ API 自動化診斷系統",
            "step1": "第一步：選擇業務類別與體系",
            "step2": "第二步：貼入待測資料",
            "btn": "🚀 開始執行分析",
            "dl": "📂 下載分析報告"
        },
        "English": {
            "header": "🛡️ API Automated Validator",
            "step1": "Step 1: Category & Series",
            "step2": "Step 2: Paste Payload",
            "btn": "🚀 Run Analysis",
            "dl": "📂 Download Report"
        }
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

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("❌ Secrets 中找不到 GEMINI_API_KEY")
    st.stop()

# ==========================================
# 4. 主介面：業務分流選擇
# ==========================================
st.title(T["header"])

st.subheader(T["step1"])
col_cat, col_ser = st.columns(2)

with col_cat:
    main_category = st.radio("選擇業務大類：", ["訂單類 (Order)", "發票類 (Invoice)"], horizontal=True)
    is_order = "訂單" in main_category
    cat_key = "Order" if is_order else "Invoice"
    data_format = "JSON" if is_order else "XML"

with col_ser:
    if is_order:
        series_option = st.selectbox("選擇系列：", ["C系列 (C0403, C0503...)", "F系列 (F0403, F0503...)"])
    else:
        series_option = st.selectbox("選擇系列：", ["C系列 (C0401, C0501...)", "F系列 (F0401, F0501...)"])
    ser_key = "C" if "C系列" in series_option else "F"

# 顯示目前選定的邏輯路徑
st.info(f"📋 當前檢查：**{main_category}** | 系列：**{ser_key}** | 格式：**{data_format}**")
st.divider()

# ==========================================
# 5. 輸入與分析區
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.subheader(f"{T['step2']} ({data_format})")
    user_input = st.text_area("Payload Data:", height=450)
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.subheader("🔍 診斷結果")
    if analyze_btn and user_input:
        spec_context = load_spec_data(cat_key, ser_key)
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家。當前業務為：{main_category}，格式為：{data_format}。
                請嚴格根據此規範校對：
                {spec_context}
                
                待分析資料：
                {user_input}
                
                任務：
                1. 檢查規範與欄位正確性。
                2. 標註對應的 [ErrorCode]。
                3. 使用 {lang_choice} 回覆分析結果。
                """
                with st.spinner(f"正在透過 {m_name} 分析中..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                break 
            except:
                continue

        if final_report:
            st.markdown(final_report)
            st.divider()
            st.download_button(T["dl"], data=final_report, file_name=f"Report_{cat_key}_{ser_key}.txt")
