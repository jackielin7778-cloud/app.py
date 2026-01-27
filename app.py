import streamlit as st
import google.generativeai as genai

# --- 頁面配置 ---
st.set_page_config(page_title="API 整合測試助手", layout="wide")

st.title("🛡️ API 預上線自動化檢測系統")
st.markdown("請在左側輸入 API Key，並在下方貼入 JSON 內容進行驗證。")

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.divider()
    default_spec = """1. 必須是有效的 JSON 格式。
2. 必填欄位: client_id, order_amount, items。
3. order_amount 必須大於 0。"""
    spec_input = st.text_area("管理員定義的驗證規則：", value=default_spec, height=200)

# --- 主畫面佈局 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 貼入測試內容")
    content_to_check = st.text_area("JSON Payload:", height=400, placeholder='{"client_id": "test_001", ...}')

with col2:
    st.subheader("2. 分析結果")
    check_button = st.button("🚀 開始執行自動化分析")
    
    if check_button:
        if not api_key:
            st.error("❌ 請在左側輸入 API Key")
        elif not content_to_check:
            st.warning("⚠️ 請貼入要檢查的內容")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # 改用配額最穩定的 1.5 Flash 版本
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""你是一位嚴格的 API 測試專家。
請根據以下【規格】檢查【內容】：
規格：
{spec_input}

內容：
{content_to_check}

請務必回覆：
1. 是否符合規格？
2. 哪裡錯了？(具體到欄位與原因)
3. 提供修正後的正確 JSON 範例。"""
                
                with st.spinner('Gemini 1.5 正在為您掃描格式...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)
                    
            except Exception as e:
                # 專門處理 429 額度問題
                if "429" in str(e):
                    st.error("🚀 伺服器太忙了！(Error 429)")
                    st.info("由於免費版 API 有頻率限制，請等待約 60 秒後再點擊一次按鈕。")
                else:
                    st.error(f"分析失敗，錯誤訊息：{str(e)}")

# --- 底部 ---
st.divider()
st.caption("Powered by Gemini 1.5 Flash | 穩定版服務路徑")
