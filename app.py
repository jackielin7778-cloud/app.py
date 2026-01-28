import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 核心功能：讀取 CSV 規則與錯誤碼
# ==========================================
def load_context_data():
    """從 CSV 載入業務邏輯與錯誤碼，作為 AI 的參考書"""
    context = ""
    
    # 載入 API 業務規則
    if os.path.exists("rules.csv"):
        rules_df = pd.read_csv("rules.csv")
        context += "【1. API 業務規範細則】:\n" + rules_df.to_string(index=False) + "\n\n"
    
    # 載入錯誤碼對照表
    if os.path.exists("error_codes.csv"):
        errors_df = pd.read_csv("error_codes.csv")
        context += "【2. 公司標準錯誤碼對照表 (Error Codes)】:\n" + errors_df.to_string(index=False) + "\n"
        
    return context if context else "目前無外部規則參考，請進行一般性邏輯檢查。"

# ==========================================
# 2. 介面初始化與語系切換
# ==========================================
st.set_page_config(page_title="AI API Validator", layout="wide", page_icon="🛡️")

# 多語系字典
LANG_DICT = {
    "繁體中文": {
        "header": "🛡️ API 自動化診斷系統 (企業版)",
        "sidebar_diag": "🛠️ 系統診斷",
        "input_label": "1. 貼入待測資料 (JSON):",
        "output_label": "2. AI 診斷報告與建議:",
        "analyze_btn": "🚀 開始執行分析",
        "download_btn": "📂 下載 TXT 報告",
        "status_ok": "API 額度：正常",
        "status_limit": "API 額度：受限 (請稍候)",
        "wait_msg": "AI 正在對照規則表中..."
    },
    "English": {
        "header": "🛡️ AI API Validator (Enterprise)",
        "sidebar_diag": "🛠️ Diagnostics",
        "input_label": "1. Paste JSON Data:",
        "output_label": "2. AI Diagnosis & Suggestions:",
        "analyze_btn": "🚀 Run Analysis",
        "download_btn": "📂 Download TXT Report",
        "status_ok": "API Quota: Healthy",
        "status_limit": "API Quota: Limited",
        "wait_msg": "AI is cross-referencing rules..."
    }
}

with st.sidebar:
    lang_choice = st.selectbox("🌐 Language / 語系", ["繁體中文", "English"])
    T = LANG_DICT[lang_choice]

# ==========================================
# 3. 權限驗證 (邀請碼機制)
# ==========================================
ACCESS_CODE = "TEST2026"  # 教材預設密碼
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🛡️ Secure Access")
    user_pwd = st.text_input("Enter Access Code / 請輸入邀請碼:", type="password")
    if st.button("Login"):
        if user_pwd == ACCESS_CODE:
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Invalid Code / 邀請碼錯誤")
    st.stop()

# ==========================================
# 4. API 金鑰與後台監測
# ==========================================
# 從 Streamlit Cloud 的 Secrets 取得金鑰
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ 找不到 API 金鑰。請在 Streamlit Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

genai.configure(api_key=api_key)

with st.sidebar:
    st.divider()
    with st.expander(T["sidebar_diag"]):
        # 簡易探針：測試 API 是否被限流
        try:
            test_m = genai.GenerativeModel('gemini-1.5-flash')
            test_m.generate_content("ping", generation_config={"max_output_tokens": 1})
            st.success(T["status_ok"])
        except:
            st.warning(T["status_limit"])
    
    if st.button("Logout / 登出"):
        st.session_state['authenticated'] = False
        st.rerun()

# ==========================================
# 5. 主程式介面
# ==========================================
st.title(T["header"])

col1, col2 = st.columns(2)

with col1:
    st.subheader(T["input_label"])
    user_input = st.text_area("JSON Content:", height=450, placeholder='{"order_id": "123", ...}')
    analyze_btn = st.button(T["analyze_btn"])

with col2:
    st.subheader(T["output_label"])
    
    if analyze_btn and user_input:
        # 模型自動備援 (2.0 Lite -> 1.5 Flash)
        models = ['gemini-2.0-flash-lite', 'gemini-1.5-flash']
        report_content = ""
        
        # 載入 CSV 內容作為上下文
        context_data = load_context_data()
        
        for m_name in models:
            try:
                model = genai.GenerativeModel(m_name)
                # 組合 Prompt
                prompt = f"""
                你現在是一位資深的 API 測試專家。請根據提供的「規範」來審核使用者的「測試資料」。
                
                {context_data}
                
                使用者測試資料：
                {user_input}
                
                分析要求：
                1. 若資料違反「業務規範細則」，請明確指出。
                2. 若符合任何「公司標準錯誤碼」，請務必標註 [ErrorCode] 代碼。
                3. 請提供修正後的 JSON 建議範本。
                4. 回覆語言：{lang_choice}。
                """
                
                with st.spinner(T["wait_msg"]):
                    response = model.generate_content(prompt)
                    report_content = response.text
                    break
            except Exception as e:
                continue # 若失敗則嘗試下一模型
        
        if report_content:
            st.session_state['report_cache'] = report_content
        else:
            st.error("❌ 無法取得分析結果，可能是 API 額度已滿，請稍後再試。")

    # 顯示結果與下載
    if st.session_state.get('report_cache'):
        st.markdown(st.session_state['report_cache'])
        st.divider()
        st.download_button(
            label=T["download_btn"],
            data=st.session_state['report_cache'],
            file_name=f"Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# 頁尾
st.caption(f"© 2026 Corporate API Validator | Rules-Driven AI | Last Login: {datetime.now().strftime('%Y-%m-%d')}")
