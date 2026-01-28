import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：根據選擇載入對應規格
# ==========================================
def load_spec_data(api_series):
    context = ""
    # 根據選取的系列決定讀取哪個檔案
    file_name = f"rules_{api_series}.csv"
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        context += f"【1. {api_series} 系列業務規範細則】:\n{df.to_string(index=False)}\n\n"
    else:
        context += f"⚠️ 警告：找不到 {file_name} 規格檔，將進行一般邏輯檢查。\n\n"
    
    # 載入通用的錯誤碼表
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【2. 公司標準錯誤碼對照表】:\n" + errors_df.to_string(index=False) + "\n"
        
    return context

# ==========================================
# 2. 介面與分類選單設定
# ==========================================
st.set_page_config(page_title="AI API Validator Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.title("⚙️ 系統設定")
    lang_choice = st.selectbox("🌐 語系 (Language)", ["繁體中文", "English"])
    
    st.divider()
    st.subheader("📂 API 類別選擇")
    
    # 使用者選擇大類
    category = st.radio(
        "選擇檢查體系：",
        ["C系列 (C/D代號)", "F系列 (F/G代號)"],
        help="C系列包含開立、作廢、註銷發票及折讓；F系列亦同。"
    )
    
    # 內部代號轉換
    series_code = "C" if "C系列" in category else "F"
    
    # 顯示詳細代號讓使用者確認
    if series_code == "C":
        st.caption("包含代號：C0403, C0503, C0703, D0403, D0503")
    else:
        st.caption("包含代號：F0403, F0503, F0703, G0403, G0503")

    T = {
        "繁體中文": {"header": "🛡️ API 自動化診斷系統", "btn": "🚀 執行分析", "dl": "📂 下載報告"},
        "English": {"header": "🛡️ API Automated Validator", "btn": "🚀 Run Analysis", "dl": "📂 Download Report"}
    }[lang_choice]

# ==========================================
# 3. 權限與 API 設定
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
# 4. 主介面：全自動分析與跳轉邏輯
# ==========================================
st.title(T["header"])
st.info(f"當前檢查標的：**{category}**")

col1, col2 = st.columns(2)

with col1:
    user_input = st.text_area("待測 JSON 資料:", height=450, placeholder='請貼入 JSON 內容...')
    analyze_btn = st.button(T["btn"])

with col2:
    if analyze_btn and user_input:
        # 取得對應系列的規則文字
        context_data = load_spec_data(series_code)
        
        # 自動路由模型順序
        priority_models = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        final_result = ""
        success_model = ""

        for m_name in priority_models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                你是 API 專家，請嚴格根據以下【{series_code} 系列】規範進行審核：
                {context_data}
                
                待測資料：
                {user_input}
                
                分析要求：
                1. 檢查是否符合該系列特定的欄位與邏輯要求。
                2. 若有錯誤，標註 [ErrorCode] 並給予解決建議。
                3. 請使用 {lang_choice} 回覆。
                """
                with st.spinner(f"正在以 {m_name} 進行規格校對..."):
                    response = model.generate_content(prompt)
                    final_result = response.text
                    success_model = m_name
                break 
            except Exception:
                continue
        
        if final_result:
            st.caption(f"💡 引擎狀態: {success_model} 運作正常")
            st.session_state['report'] = final_result
            st.markdown(final_result)
            st.divider()
            st.download_button(T["dl"], data=final_result, file_name=f"API_{series_code}_Report.txt")
        else:
            st.error("所有 AI 模型暫時無法連線，請稍後再試。")
