import streamlit as st
import google.generativeai as genai

# --- 頁面設定 ---
st.set_page_config(page_title="API 測試門戶", page_icon="🧪")
st.title("🛡️ 客戶 API 預上線檢測系統")
st.markdown("請在上傳前將您的 API Payload 貼在下方，Gemini 將為您進行即時審核。")

# --- 側邊欄：設定 ---
with st.sidebar:
    st.header("設定")
    api_key = st.text_input("請輸入 Gemini API Key", type="password")
    st.info("此工具由 Gemini 1.5 Flash 驅動，提供毫秒級的內容審核。")

# --- 主畫面 ---
target_spec = st.text_area("請定義你的 API 規格 (或由管理員預設)", placeholder="例如：id 必須是字串，amount 必須是正整數...")

user_payload = st.text_area("👉 請貼入你要測試的 JSON 內容：", height=250)

if st.button("🚀 開始檢測"):
    if not api_key:
        st.error("請先在左側輸入 API Key！")
    elif not user_payload:
        st.warning("請貼入內容再進行測試。")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            你是一位專業的 API 測試官。
            
            這是我們的 API 標準規格：
            {target_spec}
            
            這是客戶提供的內容：
            {user_payload}
            
            請嚴格執行以下三點：
            1. 檢查內容是否符合規格。
            2. 回覆客戶內容中哪些欄位錯誤、為什麼錯。
            3. 提供修改後的正確方向與範例程式碼。
            """
            
            with st.spinner('Gemini 正在深度分析中...'):
                response = model.generate_content(prompt)
                st.subheader("分析結果")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"發生錯誤：{e}")

st.divider()
st.caption("Powered by Gemini 1.5 Flash | 您的資料僅供本次即時測試使用")