import ssl  # Ensure the ssl module is explicitly imported for environments that need it
import os
import uvicorn
import openai
import PyPDF2
from docx import Document
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Инициализация клиента OpenAI с использованием новой версии API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
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
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
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

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext == "docx":
        text = extract_text_from_docx(file)
    elif ext == "pdf":
        text = extract_text_from_pdf(file)
    else:
        return JSONResponse(status_code=400, content={"error": "Unsupported file type."})

    prompt = PROMPT_TEMPLATE + text

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — юридический ассистент."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content
        return HTMLResponse(f"<pre style='white-space: pre-wrap; word-wrap: break-word;'>{result}</pre>")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
def read_root():
    content = """
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
    return HTMLResponse(content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
