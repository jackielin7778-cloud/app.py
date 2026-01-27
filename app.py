import streamlit as st
import google.generativeai as genai

# --- 頁面風格配置 ---
st.set_page_config(page_title="API 整合測試助手", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 關網資訊 03API 上線前自動化驗證系統")
st.write("本系統協助客戶在上線前，針對 API Payload 的「內容正確性」、「邏輯合法性」進行 AI 深度檢查。")

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.header("🔑 系統設定")
    
    # 優先從 Secrets 讀取，若無則顯示輸入框
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ 系統金鑰已自動載入")
    else:
        api_key = st.text_input("輸入 Gemini API Key", type="password")
        st.info("提示：管理員尚未設定全域金鑰，請手動輸入。")
    
    st.divider()
    st.header("📋 管理員定義規格")
    default_spec = """【必填欄位檢查】：
- sellerIdentifier: 8個數字，必須符合台灣統一編號編碼原則，字串類型
- order_amount: 數字類型，必須 > 0
- items: 列表類型，不可為空

【邏輯規則】：
- 若 items 內包含 'discount_code'，則必須有 'original_price' 欄位。
- timestamp 必須符合 ISO 8601 格式。"""
    
    spec_input = st.text_area("在此輸入 API 驗證規則：", value=default_spec, height=300)
    st.caption("提示：您可以直接用中文描述複雜的業務邏輯。")

# --- 主畫面：操作區 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 貼入待測資料")
    content_to_check = st.text_area("請貼入您的 JSON Payload：", height=450, placeholder='{\n  "client_id": "VIP_001",\n  "order_amount": 100,\n  "items": []\n}')

with col2:
    st.subheader("2. AI 診斷報告")
    if st.button("🚀 開始自動化檢測"):
        if not api_key:
            st.error("請在左側選單輸入 API Key 以啟動分析。")
        elif not content_to_check:
            st.warning("請貼入需要測試的內容。")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # 按照您的模型清單，建立優先級順序
                # 2.0-flash-lite 通常在免費版有較高的成功率
                models_to_try = [
                    'gemini-2.0-flash-lite', 
                    'gemini-2.0-flash', 
                    'gemini-3-flash-preview'
                ]
                
                response_text = ""
                used_model = ""
                
                # 自動重試機制
                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(m_name)
                        full_prompt = f"""
                        你是一位資深的 API 整合工程師。請根據【驗證規格】審核【待測內容】。
                        
                        【驗證規格】：
                        {spec_input}
                        
                        【待測內容】：
                        {content_to_check}
                        
                        請務必回覆以下三項結果：
                        1. 檢查機制結果：通過或不通過。
                        2. 錯誤明細：具體指出哪個欄位錯誤、原因為何。
                        3. 修改建議：提供一份修正後的正確 JSON 範本，並用代碼塊呈現。
                        """
                        
                        with st.spinner(f'正在調用 {m_name} 進行分析...'):
                            response = model.generate_content(full_prompt)
                            response_text = response.text
                            used_model = m_name
                            break # 成功獲取結果，跳出迴圈
                    except Exception as e:
                        if "429" in str(e):
                            continue # 流量限制，試下一個模型
                        else:
                            raise e # 其他錯誤則向上拋出

                if response_text:
                    st.success(f"✅ 檢測完成 (由 {used_model} 驅動)")
                    st.markdown(response_text)
                else:
                    st.error("❌ 所有可用模型的免費配額已耗盡。請等待 60 秒再試。")

            except Exception as e:
                st.error(f"系統異常：{str(e)}")
                if "404" in str(e):
                    st.info("提示：這通常是因為 API Key 無權限存取該模型，請檢查 Google AI Studio 設定。")

# --- 頁尾 ---
st.divider()
st.caption("© 2026 智慧 API 驗證助手 | 專為開發者與客戶對接設計")
