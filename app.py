import streamlit as st
import google.generativeai as genai

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="API 整合驗證助手", layout="wide", page_icon="🧪")

# --- 2. 存取權限控制 (邀請碼) ---
ACCESS_CODE = "TEST2026"  # 您可以更改此邀請碼

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    if st.session_state["pwd_input"] == ACCESS_CODE:
        st.session_state["authenticated"] = True
        del st.session_state["pwd_input"]
    else:
        st.error("❌ 邀請碼錯誤。")

if not st.session_state['authenticated']:
    st.title("🔒 歡迎使用 API 驗證網關")
    st.text_input("請輸入邀請碼以繼續：", type="password", key="pwd_input", on_change=check_password)
    st.stop()

# --- 3. 隱藏的驗證規則 (關鍵點) ---
# 您可以直接在程式碼中修改這些規則，客戶在網頁上看不見。
HIDDEN_SPEC = """
1. 必須是有效的 JSON 格式。
2. 必填欄位檢查：
   - client_id (string): 必須為英數組合。
   - order_amount (number): 必須大於 0。
   - items (list): 內含物件必須有 'prod_id' 與 'qty'。
3. 商業邏輯：
   - 如果 order_amount 超過 10000，必須包含 'manager_approval' 欄位。
   - 所有日期字串必須符合 YYYY-MM-DD 格式。
"""

# --- 4. 讀取 Secrets 中的 API Key ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("配置錯誤：請在 Secrets 設定 GEMINI_API_KEY。")
    st.stop()

# --- 5. 正式介面 ---
st.title("🛡️ API 預上線自動化檢測系統")
st.info("請在下方貼入您的 JSON Payload，系統將根據內部規範自動進行深度掃描。")

# 側邊欄改為僅顯示狀態
with st.sidebar:
    st.header("⚙️ 系統狀態")
    st.success("🔓 驗證規則已載入")
    st.write("目前模型：Gemini 2.0 Flash-Lite")
    if st.button("登出系統"):
        st.session_state['authenticated'] = False
        st.rerun()

# 主畫面操作
st.subheader("貼入測試內容")
content_to_check = st.text_area("JSON Payload:", height=400, placeholder='{"client_id": "test", ...}')

if st.button("🚀 開始檢測檔案內容"):
    if not content_to_check:
        st.warning("⚠️ 請貼入內容。")
    else:
        try:
            genai.configure(api_key=api_key)
            # 優先使用 Lite 版以避免 429 錯誤
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
            
            # 將隱藏規則與客戶內容結合
            prompt = f"""
            你是一位專業的 API 稽核員。
            這是我司的內部【API 規格】：
            {HIDDEN_SPEC}
            
            這是客戶提供的【待測內容】：
            {content_to_check}
            
            請嚴格對照規格，回覆：
            1. 診斷結果 (通過/不通過)
            2. 錯誤明細 (若有)
            3. 修正後的 JSON 範本
            """
            
            with st.spinner('內部規則掃描中...'):
                response = model.generate_content(prompt)
                st.success("分析完成！")
                st.markdown(response.text)
                
        except Exception as e:
            if "429" in str(e):
                st.error("目前伺服器忙碌中，請等待 60 秒再試。")
            else:
                st.error(f"分析失敗：{str(e)}")

st.divider()
st.caption("© 2026 API Validator Pro | 內部規則受保護模式")
