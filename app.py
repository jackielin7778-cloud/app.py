import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：動態讀取規則
# ==========================================
def load_spec_data(api_series):
    context = ""
    file_name = f"rules_{api_series}.csv"
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【重要：{api_series} 系列業務規範】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 無法讀取 {file_name}。\n\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：錯誤碼對照表】\n" + errors_df.to_string(index=False) + "\n"
        except:
            pass
    return context

# ==========================================
# 2. 頁面初始化與語系
# ==========================================
st.set_page_config(page_title="API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    T = {
        "繁體中文": {
            "header": "🛡️ API 自動化診斷系統",
            "step1": "第一步：選擇 API 體系與格式",
            "step2": "第二步：貼入待測資料",
            "step3": "第三步：AI 診斷結果",
            "btn": "🚀 開始執行分析",
            "dl": "📂 下載分析報告"
        },
        "English": {
            "header": "🛡️ API Automated Validator",
            "step1": "Step 1: Select Series & Format",
            "step2": "Step 2: Paste Payload",
            "step3": "Step 3: AI Diagnosis",
            "btn": "🚀 Run Analysis",
            "dl": "📂 Download Report"
        }
    }[lang_choice]
    
    st.divider()
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

# API 配置
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("❌ Secrets 中找不到 GEMINI_API_KEY")
    st.stop()

# ==========================================
# 4. 主介面：體系與格式選擇
# ==========================================
st.title(T["header"])

st.subheader(T["step1"])
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    api_option = st.selectbox(
        "選擇業務體系：",
        ["C系列 (C0403, C0503...)", "F系列 (F0403, F0503...)"]
    )
    current_series = "C" if "C系列" in api_option else "F"

with col_sel2:
    data_format = st.radio("選擇資料格式：", ["JSON", "XML"], horizontal=True)

st.divider()

# ==========================================
# 5. 輸入與分析
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.subheader(f"{T['step2']} ({data_format})")
    placeholder_text = "<Main>\n  <MessageId>C0403</MessageId>\n</Main>" if data_format == "XML" else '{"Main": {"MessageId": "C0403"}}'
    user_input = st.text_area("Payload Data:", height=450, placeholder=placeholder_text)
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.subheader(T["step3"])
    if analyze_btn and user_input:
        spec_context = load_spec_data(current_series)
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        used_model = ""

        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                # 針對 XML 強化 Prompt
                prompt = f"""
                你現在是 API 專家。目前檢查格式為：{data_format}。
                請嚴格根據以下規範校對內容：
                {spec_context}
                
                待分析資料：
                {user_input}
                
                任務要求：
                1. 若為 XML，請特別檢查標籤(Tag)閉合、階層結構與 Schema 合規性。
                2. 比對業務細則，標註對應的 [ErrorCode]。
                3. 使用 {lang_choice} 提供分析結果與修正後的範例。
                """
                with st.spinner(f"正在透過 {m_name} 分析 {data_format}..."):
                    response = model.generate_content(prompt)
                    final_report = response.text
                    used_model = m_name
                break 
            except:
                continue

        if final_report:
            st.caption(f"✅ 成功使用 {used_model} 分析完成")
            st.markdown(final_report)
            st.divider()
            st.download_button(T["dl"], data=final_report, file_name=f"Report_{current_series}.txt")
        else:
            st.error("分析失敗，請檢查資料或 API 額度。")
