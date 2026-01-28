import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF

# ==========================================
# 1. PDF 報告生成類別
# ==========================================
class API_Report_PDF(FPDF):
    def header(self):
        # 設定頁首
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'API Audit Report', ln=True, align='C')
        self.ln(10)

    def footer(self):
        # 設定頁碼
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def create_pdf(text):
    pdf = API_Report_PDF()
    pdf.add_page()
    
    # 注意：這裡使用內建字體。
    # 若要在 PDF 顯示中文，需上傳 .ttf 字型檔到 GitHub
    # 並使用 pdf.add_font('font_name', '', 'font.ttf', uni=True)
    pdf.set_font("helvetica", size=12)
    
    # 處理換行與特殊字元編碼，避免 PDF 崩潰
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    
    return pdf.output()

# ==========================================
# 2. 多語系與基礎設定
# ==========================================
LANG_DICT = {
    "繁體中文": {
        "title": "🛡️ API 自動化檢測系統",
        "btn_pdf": "📄 下載 PDF 報告",
        "btn_txt": "📂 下載 TXT 報告",
        "msg_wait": "AI 正在掃描邏輯...",
        "prompt_task": "請用 繁體中文 回覆，指出錯誤並給予 JSON 範本。"
    },
    "English": {
        "title": "🛡️ API Automated Validator",
        "btn_pdf": "📄 Download PDF",
        "btn_txt": "📂 Download TXT",
        "msg_wait": "AI is analyzing...",
        "prompt_task": "Please reply in English, point out errors and provide JSON."
    }
}

st.set_page_config(page_title="API Validator", layout="wide")
with st.sidebar:
    selected_lang = st.selectbox("🌐 Language", ["繁體中文", "English"])
    T = LANG_DICT[selected_lang]

# ==========================================
# 3. 權限驗證與 API 設定
# ==========================================
ACCESS_CODE = "TEST2026"
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# 登入邏輯
if not st.session_state['authenticated']:
    pwd = st.text_input("Access Code:", type="password")
    if st.button("Login"):
        if pwd == ACCESS_CODE:
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# 載入金鑰
api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# ==========================================
# 4. CSV 規則載入
# ==========================================
def get_rules():
    if os.path.exists("rules.csv"):
        return pd.read_csv("rules.csv").to_string(index=False)
    return "No rules available."

HIDDEN_SPEC = get_rules()

# ==========================================
# 5. 主介面 UI 與 分析邏輯
# ==========================================
st.title(T["title"])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Input")
    content = st.text_area("JSON Payload:", height=400)
    analyze_btn = st.button("🚀 Analyze")

with col2:
    st.subheader("Report")
    
    if 'report' not in st.session_state:
        st.session_state['report'] = None

    if analyze_btn and content:
        # 模型自動備援 (Fallback)
        for m_name in ['gemini-2.0-flash-lite', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"Rules:\n{HIDDEN_SPEC}\nContent:\n{content}\nTask: {T['prompt_task']}"
                with st.spinner(T["msg_wait"]):
                    response = model.generate_content(prompt)
                    st.session_state['report'] = response.text
                    break
            except:
                continue

    # 顯示報告與下載按鈕
    if st.session_state['report']:
        st.markdown(st.session_state['report'])
        st.divider()
        
        # 準備 PDF 資料
        pdf_output = create_pdf(st.session_state['report'])
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(T["btn_txt"], data=st.session_state['report'], file_name="report.txt")
        with c2:
            st.download_button(T["btn_pdf"], data=bytes(pdf_output), file_name="report.pdf", mime="application/pdf")
