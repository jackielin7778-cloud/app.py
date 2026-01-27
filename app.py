import streamlit as st
import google.generativeai as genai

# --- 頁面風格配置 ---
st.set_page_config(page_title="API 整合測試助手", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ API 預上線自動化驗證網關")
st.write("本系統協助客戶在上線前，針對 API Payload 的「內容正確性」、「邏輯合法性」進行 AI 深度檢查。")

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.header("🔑 系統設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password", help="請從 Google AI Studio 獲取")
    
    st.divider()
    st.header("📋 管理員定義規格")
    default_spec = """【必填欄位檢查】：
- client_id: 字串類型
- order_amount: 數字類型，必須 > 0
- items: 列表類型，不可為空

【邏輯規則】：
- 若 items 內包含 'discount_code'，則必須有 'original_price' 欄位。
- timestamp 必須符合 ISO 8601 格式。"""
    
    spec_input = st.text_area("在此輸入 API 驗證規則：", value=default_spec, height=300)
    st.caption("提示：您可以直接用中文描述複雜的業務邏輯。")

# --- 主畫面：操作區 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 貼入待測資料")
    content_to_check = st.text_area("請貼入您的 JSON Payload：", height=450, placeholder='{\n  "client_id": "VIP_001",\n  "order_amount": 100,\n  "items": []\n}')

with col2:
    st.subheader("2. AI 診斷報告")
    if st.button("🚀 開始自動化檢測"):
        if not api_key:
            st.error("請在左側選單輸入 API Key 以啟動分析。")
        elif not content_to_check:
            st.warning("請貼入需要測試的內容。")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # 按照您的模型清單，建立優先級順序
                # 2.0-flash-lite 通常在免費版有較高的成功率
                models_to_try = [
                    'gemini-2.0-flash-lite', 
                    'gemini-2.0
