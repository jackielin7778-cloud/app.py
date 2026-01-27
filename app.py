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
    # 你可以預先在這裡寫入你的 API 規則，客戶就不用自己輸入
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
    genai.configure(api_key=api_key)
    
    # 使用 1.5 Flash，這是目前主流且支援度最高的名稱
    model_name = 'gemini-1.5-flash' 
    
    # 建立模型
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
    )
    
    with st.spinner(f'正在使用 {model_name} 進行深度分析...'):
        # 確保 prompt 內容不是空的
        response = model.generate_content(prompt)
        st.success("分析完成！")
        st.markdown(response.text)

except Exception as e:
    # 如果還是失敗，顯示更詳細的錯誤供我們排查
    st.error(f"系統錯誤：{str(e)}")
    st.info("提示：請確認您的 API Key 是否來自 Google AI Studio，且具備 Gemini 1.5 Flash 的存取權限。")
                
                # 建立結構化的 Prompt
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
                
                with st.spinner('Gemini 正在逐行掃描內容...'):
                    response = model.generate_content(prompt)
                    st.success("分析完成！")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"分析失敗，錯誤訊息: {str(e)}")

# --- 底部說明 ---
st.divider()
st.caption("© 2024 API 自動化測試網關 | 建議在正式環境串接前，先通過此處驗證。")
