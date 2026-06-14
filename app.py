import os
from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google import genai
from google.genai import types

app = FastAPI()
# 尋找與 app.py 同層級的 templates 資料夾
templates = Jinja2Templates(directory="templates")

# 🔴 請在此處替換成你的 Gemini API Key
GEMINI_API_KEY = "gemini_api_key"

# 初始化 Gemini 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# 系統提示詞：打造萬能摩擦力解題專家（新增圖文辨識引導）
SYSTEM_PROMPT = """你是一個頂尖的物理教授，專門精準解答各種「摩擦力」相關題目。
不論使用者提供的是「文字描述」或是「電路、力學結構的題目圖片（如水平面、斜面、拉力帶夾角、多物體連接體等）」，你都必須仔細看懂並嚴格遵循以下物理邏輯進行拆解：

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


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request,
        name="index.html",
        context={"result": None, "question": ""}
    )


@app.post("/", response_class=HTMLResponse)
async def solve_question(
        request: Request,
        question: str = Form(""),  # 改為非必填，因為使用者可能只傳圖片
        image_file: UploadFile = File(None)  # 接收前端上傳的圖片檔案
):
    try:
        # 準備好要傳給 Gemini 的內容清單
        contents_payload = []

        # 1. 檢查是否有上傳圖片，如果有，讀取圖片 bytes 並封裝
        if image_file and image_file.filename != "":
            image_bytes = await image_file.read()
            # 依據上傳的圖片類型動態設定 mime_type (例如 image/png, image/jpeg)
            mime_type = image_file.content_type if image_file.content_type else "image/jpeg"

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
            contents_payload.append(image_part)

        # 2. 檢查是否有輸入文字題目，如果有，加入清單
        if question.strip():
            contents_payload.append(question)

        # 安全機制：如果文字和圖片都沒給，直接回傳提示
        if not contents_payload:
            return templates.TemplateResponse(
                request,
                name="index.html",
                context={"result": "請輸入題目文字或上傳題目圖片！", "question": question}
            )

        # 呼叫 Gemini 多模態模型
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_payload,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,  # 保持計算精準度
            ),
        )
        result = response.text

    except Exception as e:
        result = f"Error: 處理請求或呼叫 Gemini API 時發生錯誤。詳細原因: {str(e)}"

    return templates.TemplateResponse(
        request,
        name="index.html",
        context={"result": result, "question": question}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)