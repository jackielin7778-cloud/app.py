import streamlit as st
import google.generativeai as genai
import json

# --- 頁面配置 ---
st.set_page_config(page_title="API 整合測試助手", page_icon="🔍", layout="wide")

# 自定義 CSS 讓介面更漂亮
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛠️ API 雙方對接驗證系統")
st.info("本系統由 Gemini 1.5 Flash 驅動，專門用於上線前的 API 檔案內容與邏輯檢查。")

# --- 側邊欄：管理與金鑰 ---
with st.sidebar:
    st.header("🔑 認證設定")
    api_key = st.text_input("請輸入您的 Gemini API Key", type="password")
    
    st.divider()
    st.header("📋 預設 API 規格")
    default_spec = """
    1. 必須是有效的 JSON 格式。
    2. 必填欄位: 'client_id' (string), 'order_amount' (number), 'items' (list)。
    3. order_amount 必須大於 0。
    4. items 列表內每個物件必須包含 'prod_id' 與 'qty'。
    """
    spec_input = st.text_area("管理員定義的驗證規則：", value=default_spec, height=200)

# --- 主畫面：操作區 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 貼入測試內容")
    content_to_check = st.text_area("請在此貼入準備傳送的 API Payload (JSON):", height=400, placeholder='{"client_id": "test_001", ...}')

with col2:
    st.subheader("2. 執行自動化檢查")
    check_button = st.button("🚀 開始分析檔案內容")
    
    if check_button:
        if not api_key:
            st.error("❌ 請在側邊欄填入 API Key。")
        elif not content_to_check:
            st.warning("⚠️ 請貼入要檢查的內容。")
        else:
            try:
                # 1. 配置 API
                genai.configure(api_key=api_key)
                
                # 2. 建立模型 (使用最穩定的 1.5-flash)
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    generation_config={
                        "temperature": 0.2, # 降低隨機性，讓檢查更精確
                        "top_p": 0.95,
                        "max_output_tokens": 8192,
                    }
                )
                
                # 3. 建立結構化的 Prompt (必須在 generate_content 之前)
                prompt = f"""
                你是一位嚴格的 API 測試專家。請針對以下客戶提供的『內容』，對照『API 規格』進行檢查。
                
                【API 規格】：
                {spec_input}
                
                【客戶內容】：
                {content_to_check}
                
                請嚴格依照以下格式回覆：
                ### 🚩 1. 檔案內容檢查結果
                (判斷是否符合規範，若格式嚴重錯誤請直接指出)
                
                ### ❌ 2. 錯誤明細 (條列式)
                - 錯誤位置: 
                - 錯誤原因: 
                
                ### 💡 3. 修改建議與正確範本
                (請提供一段修正後可直接執行的 JSON 範例，並解釋為什麼這樣改)
                """
                
                # 4. 送出分析
                with st.spinner('Gemini 正在分析中...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)

            except Exception as e:
                # 捕獲並顯示錯誤
                st.error(f"分析失敗，錯誤訊息: {str(e)}")
                if "404" in str(e):
                    st.info("提示：模型名稱可能不正確或 API Key 無權限，請確認使用的是 Gemini 1.5 Flash。")

# --- 底部說明 ---
st.divider()
st.caption("© 2026 API 自動化測試網關 | Powered by Gemini 1.5 Flash")
