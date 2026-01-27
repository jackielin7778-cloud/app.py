import streamlit as st
import google.generativeai as genai

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="API 整合驗證助手", layout="wide", page_icon="🧪")

# 自定義介面美化
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 存取權限控制 ---
# 建議將此邀請碼也存入 Secrets (例如 st.secrets["ACCESS_CODE"])
ACCESS_CODE = "TEST2026" 

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    if st.session_state["pwd_input"] == ACCESS_CODE:
        st.session_state["authenticated"] = True
        del st.session_state["pwd_input"]
    else:
        st.error("❌ 邀請碼錯誤，請洽詢您的管理員。")

# 登入介面
if not st.session_state['authenticated']:
    st.title("🔒 歡迎使用 API 驗證網關")
    st.text_input("請輸入邀請碼以繼續：", type="password", key="pwd_input", on_change=check_password)
    st.stop()

# --- 3. 隱藏的驗證規則 (內建規格) ---
# 客戶在介面上看不到這些規則
HIDDEN_SPEC = """
【API 核心規範】：
1. 格式必須為標準 JSON。
2. 必填欄位：
   - client_id (string): 用戶唯一識別碼
   - order_amount (number): 訂單金額，必須大於 0
   - items (list): 訂單明細，不可為空
3. 商業邏輯限制：
   - 若 items 內單一商品 qty 大於 100，必須附帶 'bulk_order': true 標記。
   - 所有 timestamp 必須符合 ISO 8601 格式。
"""

# --- 4. 讀取 Secrets 金鑰 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("❌ 配置錯誤：請在 Streamlit Cloud Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# --- 5. 正式操作介面 ---
st.title("🛡️ API 預上線自動化檢測系統")
st.info("系統已載入內部驗證規格。請貼入您的 Payload，AI 將自動完成合規性掃描。")

with st.sidebar:
    st.header("⚙️ 系統狀態")
    st.success("🔓 存取權限已啟用")
    st.write("目前優先模型：Gemini 2.0 Flash-Lite")
    st.divider()
    if st.button("登出"):
        st.session_state['authenticated'] = False
        st.rerun()

# 主畫面操作
st.subheader("貼入測試內容")
content_to_check = st.text_area("請貼入您的 JSON Payload：", height=400, placeholder='{"client_id": "VIP_001", ...}')

if st.button("🚀 開始自動化檢測"):
    if not content_to_check:
        st.warning("⚠️ 請貼入內容後再進行檢測。")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 模型嘗試清單：2.0 Lite -> 2.0 Standard -> 3.0 Preview -> 1.5 Fallback
            models_to_try = [
                'gemini-2.0-flash-lite', 
                'gemini-2.0-flash', 
                'gemini-3-flash-preview',
                'gemini-1.5-flash'
            ]
            
            response_text = ""
            final_model = ""
            
            # 自動跳轉重試機制
            for m_name in models_to_try:
                try:
                    model = genai.GenerativeModel(m_name)
                    
                    prompt = f"""
                    你是一位資深的 API 稽核專家。請根據【內部規格】檢查客戶的【測試內容】。
                    
                    【內部規格】：
                    {HIDDEN_SPEC}
                    
                    【測試內容】：
                    {content_to_check}
                    
                    請嚴格回覆以下結構：
                    ### 🚩 診斷結果
                    (通過/不通過)
                    
                    ### ❌ 錯誤明細
                    (若有錯誤，請具體指出欄位與原因；若無則寫「無」)
                    
                    ### 💡 修正範本
                    (請提供修正後可直接使用的 JSON 代碼塊)
                    """
                    
                    with st.spinner(f'AI 正在通過 {m_name} 進行掃描...'):
                        response = model.generate_content(prompt)
                        response_text = response.text
                        final_model = m_name
                        break # 成功則跳出
                except Exception as e:
                    # 若遇 429 (流量限制) 或 404 (型號不支援)，自動試下一個
                    if "429" in str(e) or "404" in str(e):
                        continue
                    else:
                        raise e

            if response_text:
                st.success(f"✅ 檢測完成")
                st.markdown(response_text)
                # 管理員可見的偵錯訊息 (放在摺疊欄)
                with st.expander("🛠️ 診斷資訊 (僅限管理員)"):
                    st.write(f"執行模型: {final_model}")
            else:
                st.error("🚀 當前所有 AI 模型配額已滿，請等待 60 秒後重試。")

        except Exception as e:
            st.error(f"系統偵測到異常：{str(e)}")

st.divider()
st.caption("© 2026 API Validator Pro | 企業級 AI 驗證網關")
