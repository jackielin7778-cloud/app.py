import streamlit as st
import google.generativeai as genai

# --- 頁面配置 ---
st.set_page_config(page_title="API 整合測試助手", layout="wide")

st.title("🛠️ API 雙方對接驗證系統")

# --- 側邊欄 ---
with st.sidebar:
    st.header("🔑 設定")
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
    if st.button("🚀 開始檢測"):
        if not api_key:
            st.error("請輸入 API Key")
        elif not content_to_check:
            st.warning("請貼入內容")
        else:
            try:
                # 初始化
                genai.configure(api_key=api_key)
                
                # 解決 404 問題：嘗試使用最通用的名稱
               model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # 組合 Prompt (使用最安全的字串處理方式)
                prompt = f"你是API專家。請根據規則：{spec_input}，檢查以下內容：{content_to_check}。請列出錯誤並給建議。"
                
                with st.spinner('Gemini 運算中...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)

            except Exception as e:
                error_msg = str(e)
                st.error(f"分析失敗：{error_msg}")
                
                # 如果還是 404，執行診斷
                if "404" in error_msg:
                    st.info("正在嘗試為您找出可用的模型名稱...")
                    try:
                        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        st.write("您的 Key 支援的模型清單：", models)
                    except:
                        st.write("無法取得清單，請確認 API Key 是否有效。")

st.divider()
st.caption("Powered by Gemini 1.5 Flash")
