from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai
import os
from docx import Document
import PyPDF2

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_docx(file):
    doc = Document(file.file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

PROMPT_TEMPLATE = """
Ты — юридический ИИ-ассистент. Прочитай текст договора и:

1. Объясни сложные формулировки простыми словами.
2. Укажи потенциальные риски для клиента.
3. Дай советы, какие пункты стоит добавить или изменить.

Ответ структурируй по разделам:
- Простое объяснение
- Потенциальные риски
- Рекомендации

Важно: не давай юридических гарантий. Уточни, что это только ИИ-помощь.

ТЕКСТ ДОГОВОРА:
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang='ru'>
    <head>
        <meta charset='UTF-8'>
        <title>DocAI-Помощник</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; background: #f9f9f9; }
            .container { background: white; padding: 30px; border-radius: 16px; max-width: 600px; margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            h1 { color: #1f2937; text-align: center; }
            p { color: #4b5563; }
            input[type=file] { margin-top: 15px; }
            button { margin-top: 20px; background-color: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; }
            button:hover { background-color: #2563eb; }
            .disclaimer { font-size: 0.8em; color: #6b7280; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class='container'>
            <h1>DocAI-Помощник</h1>
            <p>Загрузите договор в формате DOCX или PDF, чтобы получить анализ.</p>
            <form action='/analyze' method='post' enctype='multipart/form-data'>
                <input type='file' name='file' accept='.pdf,.docx' required />
                <br/>
                <button type='submit'>Начать анализ</button>
            </form>
            <div class='disclaimer'>Это не является юридической консультацией. Используйте как вспомогательный инструмент.</div>
        </div>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    if file.filename.endswith(".docx"):
        contract_text = extract_text_from_docx(file)
    elif file.filename.endswith(".pdf"):
        contract_text = extract_text_from_pdf(file)
    else:
        return JSONResponse(content={"error": "Unsupported file format."}, status_code=400)

    prompt = PROMPT_TEMPLATE + contract_text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — юридический ассистент."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response["choices"][0]["message"]["content"]
        return HTMLResponse(f"<pre style='white-space: pre-wrap; word-wrap: break-word;'>{result}</pre>")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
