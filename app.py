try:
                genai.configure(api_key=api_key)
                
                # --- 優化後的模型嘗試清單 ---
                # 順序邏輯：
                # 1. 2.0-flash-lite (最快、最不容易爆配額)
                # 2. 2.0-flash (平衡型，推理力強)
                # 3. 3-flash-preview (最新實驗版，能力最強但最不穩定)
                # 4. 1.5-flash (經典穩定版，作為最後防線)
                models_to_try = [
                    'gemini-2.0-flash-lite', 
                    'gemini-2.0-flash', 
                    'gemini-3-flash-preview',
                    'gemini-1.5-flash'
                ]
                
                response_text = ""
                used_model = ""
                
                # 自動重試機制：直到有一個模型能動為止
                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(m_name)
                        
                        # 結合隱藏規則與內容
                        prompt = f"規格：{HIDDEN_SPEC}\n內容：{content_to_check}\n任務：精確指出錯誤點並給予正確 JSON。"
                        
                        with st.spinner(f'正在調用 {m_name} 進行深度掃描...'):
                            # 加入超時控制或簡單的生成
                            response = model.generate_content(prompt)
                            response_text = response.text
                            used_model = m_name
                            break  # 成功獲取結果，立即跳出迴圈
                            
                    except Exception as e:
                        # 如果是 429 錯誤（流量限制），則切換到下一個模型
                        if "429" in str(e):
                            continue 
                        # 如果是 404 錯誤（模型不存在），也嘗試下一個
                        elif "404" in str(e):
                            continue
                        else:
                            # 其他嚴重錯誤（如 API Key 異常）則直接報錯
                            raise e

                if response_text:
                    st.success(f"✅ 檢測完成 (由 {used_model} 驅動)")
                    st.markdown(response_text)
                else:
                    st.error("🚀 所有可用模型的免費配額目前均已耗盡，請稍候 60 秒再試。")

            except Exception as e:
                st.error(f"分析失敗，系統訊息：{str(e)}")
