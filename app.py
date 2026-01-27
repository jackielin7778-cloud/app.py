import streamlit as st
import google.generativeai as genai

# --- 頁面配置 ---
st.set_page_config(page_title="API 整合測試助手", layout="wide")

st.title("🛡️ API 預上線自動化檢測系統")

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.divider()
    default_spec = "1. 必須是 JSON 格式\n2. 必填欄位: client_id, order_amount"
    spec_input = st.text_area("管理員定義的驗證規則：", value=default_spec, height=200)

# --- 主畫面 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 貼入測試內容")
    content_to_check = st.text_area("JSON Payload:", height=400)

with col2:
    st.subheader("2. 分析結果")
    if st.button("🚀 開始分析"):
        if not api_key:
            st.error("請輸入 API Key")
        elif not content_to_check:
            st.warning("請貼入內容")
        else:
            try:
                # 配置 API
                genai.configure(api_key=api_key)
                
                # 關鍵修正：直接指定你清單中確認存在的型號
                # 如果 2.0-flash 還是 429，可以換成 2.0-flash-lite
                model_name = 'gemini-2.0-flash'
                model = genai.GenerativeModel(model_name)
                
                prompt = f"規則：{spec_input}\n內容：{content_to_check}\n任務：檢查格式並給予修正建議。"
                
                with st.spinner(f'正在調用 {model_name}...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)

            except Exception as e:
                err = str(e)
                if "429" in err:
                    st.error("❌ 流量過大：目前免費額度用完，請等 60 秒再試。")
                elif "404" in err:
                    st.error("❌ 模型路徑錯誤：請聯絡管理員確認型號。")
                else:
                    st.error(f"分析失敗：{err}")

st.divider()
st.caption("Powered by Gemini 2.0 Flash | 2026 Developer Edition")
