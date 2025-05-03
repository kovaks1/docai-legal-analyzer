import ssl
import os
import uvicorn
import openai
import PyPDF2
import logging
from docx import Document
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

MAX_FILE_SIZE_MB = 5


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
    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return JSONResponse(status_code=413, content={"error": "Файл слишком большой. Максимум 5MB."})

    if file.content_type not in ("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        return JSONResponse(status_code=400, content={"error": "Неподдерживаемый тип файла."})

    ext = file.filename.split(".")[-1].lower()
    try:
        if ext == "docx":
            text = extract_text_from_docx(file)
        elif ext == "pdf":
            text = extract_text_from_pdf(file)
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported file type."})
    except Exception as e:
        logging.exception("Ошибка при чтении файла")
        return JSONResponse(status_code=500, content={"error": "Не удалось прочитать файл."})

    if not text.strip():
        return JSONResponse(status_code=400, content={"error": "Не удалось извлечь текст из документа."})

    prompt = PROMPT_TEMPLATE + text

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — юридический ассистент."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang='ru'>
        <head>
            <meta charset='UTF-8'>
            <title>Результат анализа</title>
            <style>
                html {{
                    scroll-behavior: smooth;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    background: #f3f4f6;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .result-card {{
                    background: #ffffff;
                    border-radius: 20px;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    padding: 30px 25px;
                    text-align: left;
                    white-space: pre-wrap;
                    overflow-y: auto;
                    max-height: 90vh;
                    animation: fadeIn 1s ease-in-out;
                }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                h1 {{
                    color: #1f2937;
                    font-size: 1.4rem;
                    margin-bottom: 20px;
                }}
                .back-link {{
                    display: inline-block;
                    margin-top: 20px;
                    color: #3b82f6;
                    text-decoration: none;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class='result-card'>
                <h1>Результат анализа</h1>
                {result}
                <a href='/' class='back-link'>← Назад</a>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logging.exception("Ошибка при обращении к OpenAI")
        return JSONResponse(status_code=500, content={"error": "Не удалось обработать запрос."})


@app.get("/")
def read_root():
    # шаблон остался без изменений
    ...

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

