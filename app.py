import streamlit as st
import google.generativeai as genai

# --- 頁面配置 ---
st.set_page_config(page_title="API 測試門戶", layout="wide")

st.title("🛡️ API 預上線自動化檢測系統")
st.markdown("請在下方輸入 API Key 與測試內容，系統將自動進行規格校對。")

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
            st.error("❌ 請輸入 API Key")
        elif not content_to_check:
            st.warning("⚠️ 請貼入要檢查的內容")
        else:
            try:
                # 1. 配置 API
                genai.configure(api_key=api_key)
                
                # 2. 建立模型 (使用您清單中確認可用的 2.0 版本)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. 建立 Prompt
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
                
                with st.spinner('Gemini 2.0 深度檢查中...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"分析失敗，錯誤訊息：{str(e)}")

# --- 底部 ---
st.divider()
st.caption("Powered by Gemini 2.0 Flash | 2026 API Validator Beta")
