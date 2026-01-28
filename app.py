import streamlit as st
import google.generativeai as genai

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="API 整合驗證助手", layout="wide", page_icon="🧪")

# --- 2. 存取權限控制 (邀請碼) ---
# 你可以在這裡更改你的邀請碼
ACCESS_CODE = "TEST2026" 

# 初始化 Session State (紀錄登入狀態)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    if st.session_state["pwd_input"] == ACCESS_CODE:
        st.session_state["authenticated"] = True
        del st.session_state["pwd_input"] # 登入後刪除密碼緩存
    else:
        st.error("❌ 邀請碼錯誤，請洽詢您的客戶經理。")

# 如果尚未通過驗證，顯示登入畫面
if not st.session_state['authenticated']:
    st.title("🔒 歡迎使用 API 驗證網關")
    st.text_input("請輸入邀請碼以繼續：", type="password", key="pwd_input", on_change=check_password)
    st.stop() # 停止執行後續程式碼

# --- 3. 通過驗證後的正式介面 ---
st.title("🛡️ API 預上線自動化檢測系統")

# 讀取 Secrets 中的 API Key
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("系統配置錯誤：請管理員於 Secrets 設定 GEMINI_API_KEY。")
    st.stop()

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("📋 驗證規格管理")
    st.success("🔓 存取權限已啟用")
    default_spec = """1. 必須是有效的 JSON 格式。
2. 必填欄位: client_id (string), order_amount (number)。
3. order_amount 必須大於 0。"""
    spec_input = st.text_area("管理員定義的驗證規則：", value=default_spec, height=300)
    
    if st.button("登出"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- 主畫面佈局 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 貼入待測資料")
    content_to_check = st.text_area("JSON Payload:", height=450, placeholder='{"client_id": "test", ...}')

with col2:
    st.subheader("2. AI 診斷報告")
    if st.button("🚀 開始自動化分析"):
        if not content_to_check:
            st.warning("⚠️ 請貼入內容後再進行檢測。")
        else:
            try:
                genai.configure(api_key=api_key)
                # 使用自動嘗試機制，確保穩定性
                models_to_try = ['gemini-2.0-flash-lite', 'gemini-1.5-flash']
                
                success = False
                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(m_name)
                        prompt = f"規則：{spec_input}\n內容：{content_to_check}\n任務：精確指出錯誤點並給予正確 JSON 範本。"
                        
                        with st.spinner(f'AI 正在執行深度分析...'):
                            response = model.generate_content(prompt)
                            st.success(f"檢測完成！")
                            st.markdown(response.text)
                            success = True
                            break
                    except:
                        continue
                
                if not success:
                    st.error("目前 API 配額已達上限，請 60 秒後再試。")
                    
            except Exception as e:
                st.error(f"系統錯誤：{str(e)}")

st.divider()
st.caption("© 2026 API Validator Pro | 已啟用傳輸層加密保護")
