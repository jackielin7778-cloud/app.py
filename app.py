import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：動態讀取規格
# ==========================================
def load_spec_data(cat_key, series_key):
    context = ""
    # 預期檔案：rules_Order_C.csv, rules_Order_F.csv, rules_Invoice_C.csv, rules_Invoice_F.csv
    file_name = f"rules_{cat_key}_{series_key}.csv"
    
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            context += f"【審核規範：{cat_key} / {series_key}】\n{df.to_string(index=False)}\n\n"
        except:
            context += f"⚠️ 無法讀取檔案：{file_name}\n"
    
    if os.path.exists("error_codes.csv"):
        try:
            errors_df = pd.read_csv("error_codes.csv")
            context += "【參考：通用錯誤碼】\n" + errors_df.to_string(index=False) + "\n"
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
            "step1": "第一步：選擇檢查目標",
            "step2": "第二步：貼入待測資料",
            "btn": "🚀 執行 AI 診斷",
            "dl": "📂 下載分析報告"
        },
        "English": {
            "header": "🛡️ API Automated Validator",
            "step1": "Step 1: Select Target",
            "step2": "Step 2: Paste Data",
            "btn": "🚀 Run AI Diagnosis",
            "dl": "📂 Download Report"
        }
    }[lang_choice]

# ==========================================
# 3. 權限與 API 配置
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
    st.error("❌ 找不到 API Key")
    st.stop()

# ==========================================
# 4. 主介面：單一選擇清單
# ==========================================
st.title(T["header"])

st.subheader(T["step1"])
# 將所有分類整合成單一選單
selection = st.selectbox(
    "請選擇 API 類型：",
    [
        "訂單類 - C系列 (JSON)",
        "訂單類 - F系列 (JSON)",
        "發票類 - C系列 (XML)",
        "發票類 - F系列 (XML)"
    ]
)

# 解析選擇結果
if "訂單類" in selection:
    cat_key = "Order"
    data_format = "JSON"
else:
    cat_key = "Invoice"
    data_format = "XML"

ser_key = "C" if "C系列" in selection else "F"

# 顯示目前狀態
st.info(f"✅ 已選定：**{cat_key}** 體系 | **{ser_key}** 系列 | 預期格式：**{data_format}**")
st.divider()

# ==========================================
# 5. 分析區
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.subheader(f"{T['step2']} ({data_format})")
    user_input = st.text_area("資料內容 (Input):", height=450)
    analyze_btn = st.button(T["btn"], use_container_width=True)

with col_out:
    st.subheader("📋 診斷報告")
    if analyze_btn and user_input:
        spec_context = load_spec_data(cat_key, ser_key)
        # 模型自動路由
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_report = ""
        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 校對專家。當前業務：{cat_key}, 系列：{ser_key}。
                預期資料格式：{data_format}。
                請依據以下規範進行校對：
                {spec_context}
                
                待分析資料：
                {user_input}
                
                分析任務：
                1. 確認資料是否符合 {data_format} 語法與業務規則。
                2. 發現錯誤請標註 [ErrorCode]。
                3. 使用 {lang_choice} 回覆結果與修正建议。
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
            st.download_button(T["dl"], data=final_report, file_name=f"Audit_{cat_key}_{ser_key}.txt")
