import streamlit as st
from google import genai
from google.genai import types

# 1. 網頁基本設定
st.set_page_config(page_title="摩擦力 AI 智慧解題系統", page_icon="🚀", layout="centered")

# 2. 系統提示詞：維持最專業的物理教授邏輯
SYSTEM_PROMPT = """你是一個頂尖的物理教授，專門精準解答各種「摩擦力」相關題目。
不論使用者提供的是「文字描述」或是「力學結構的題目圖片（如水平面、斜面、拉力帶夾角、多物體連接體等）」，你都必須仔細看懂並嚴格遵循以下物理邏輯進行拆解：

1. 【題目解析】：提取並列出已知條件（如質量 m、外力 F、角度 θ、靜摩擦係數 μs、動摩擦係數 μk、重力加速度 g=9.8 或 10）。如果是圖片，請先簡述你從圖片中辨識到的物體結構與數據。
2. 【受力分析與正向力 N】：
   - 水平面垂直無外力：$N = mg$
   - 斜面場景：$N = mg \\cos\\theta$
   - 有斜向拉力/推力：精準進行正交分解，計算出正確的 $N$。
3. 【計算最大靜摩擦力】：計算 $f_{s,\\max} = \\mu_s \\times N$。
4. 【狀態判斷】：比較順著運動方向的外力合力 $F_{\\text{parallel}}$ 與 $f_{s,\\max}$ 的大小：
   - 若 $F_{\\text{parallel}} \\le f_{s,\\max}$：物體保持「靜止」，此時靜摩擦力 $f_s = F_{\\text{parallel}}$，加速度 $a = 0$。
   - 若 $F_{\\text{parallel}} > f_{s,\\max}$：物體開始「運動」，此時摩擦力轉變為動摩擦力 $f_k = \\mu_k \\times N$，並依據 $F_{\\text{parallel}} - f_k = ma$ 計算出加速度 $a$。
5. 【完整答案】：明確標示出「物體狀態」、「所受摩擦力大小與方向」以及「加速度」。

請使用繁體中文回答，並嚴格使用 Markdown 格式輸出。數學公式與變數請務必用 $...$ (行內公式) 或 $$...$$ (獨立行公式) 包起來，以便網頁美化渲染。解題步驟要條理清晰、邏輯嚴密。"""

# 3. 標題區
st.title("摩擦力 AI 智慧解題系統 🚀")
st.caption("支援水平面、斜面、拉力夾角等各類題型。您可以直接輸入題目或上傳圖片！")

# 檢查雲端後台是否有設定 Secrets 金鑰
has_cloud_key = "GEMINI_API_KEY" in st.secrets

# 4. 建立輸入表單區
with st.form("solver_form"):
    # 🔒 密碼形式的金鑰輸入框（若後台已有 Key，則這裡變成選填）
    if has_cloud_key:
        api_key = st.text_input("Gemini API 金鑰 (系統已在後台自動安全載入，此處可留空 🔓)：", type="password")
    else:
        api_key = st.text_input("Gemini API 金鑰 (必填 🔒)：", type="password", placeholder="請貼上您的 AIzaSy... 金鑰")

    # 文字題目輸入
    question = st.text_area("請輸入題目文字描述（若僅有圖片可留空）：",
                            placeholder="例如：一個質量 5kg 的木塊放在水平面上...")

    # 📷 圖片上傳按鈕
    uploaded_file = ["png", "jpg", "jpeg"]
    image_file = st.file_uploader("上傳題目圖片（支援手寫筆記、考卷截圖、課本拍照）：", type=uploaded_file)

    # 送出按鈕
    submit_button = st.form_submit_button(label="開始 AI 精準解題 🚀")

# 5. 觸發解題邏輯
if submit_button:
    # ✨ 關鍵改動：優先讀取後台 Secrets 金鑰，若沒有才拿網頁輸入框的 Key
    final_api_key = st.secrets.get("GEMINI_API_KEY", api_key.strip())

    if not final_api_key:
        st.error("錯誤：請務必輸入 Gemini API 金鑰，或請管理員在雲端後台設定 Secrets！")
    elif not question.strip() and not image_file:
        st.warning("請輸入題目文字或上傳題目圖片！")
    else:
        with st.spinner("AI 老師正在瘋狂受力分析與計算中，請稍候..."):
            try:
                contents_payload = []

                if image_file:
                    image_bytes = image_file.read()
                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=image_file.type
                    )
                    contents_payload.append(image_part)
                    st.image(image_file, caption="您上傳的題目圖片", use_container_width=True)

                if question.strip():
                    contents_payload.append(question)

                # 初始化連線
                client = genai.Client(api_key=final_api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                    ),
                )

                # 6. 輸出結果
                st.success("✨ AI 老師解題分析完成！")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"呼叫 API 時發生錯誤，請確認金鑰是否有效。\n詳細原因: {str(e)}")