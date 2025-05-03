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
client = openai.OpenAI(api_key=os.getenv("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"))
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
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang='ru'>
        <head>
            <meta charset='UTF-8'>
            <title>Результат анализа</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: #f3f4f6;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .result-card {
                    background: #ffffff;
                    border-radius: 20px;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    padding: 30px 25px;
                    text-align: left;
                    white-space: pre-wrap;
                    overflow-y: auto;
                    max-height: 90vh;
                }
                h1 {
                    color: #1f2937;
                    font-size: 1.4rem;
                    margin-bottom: 20px;
                }
                .back-link {
                    display: inline-block;
                    margin-top: 20px;
                    color: #3b82f6;
                    text-decoration: none;
                }
                .back-link:hover {
                    text-decoration: underline;
                }
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
            body {
                font-family: Arial, sans-serif;
                background: #f3f4f6;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: #ffffff;
                border-radius: 20px;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                padding: 30px 25px;
                text-align: center;
            }
            h1 {
                color: #1f2937;
                font-size: 1.6rem;
                margin-bottom: 10px;
            }
            h2 {
                color: #4b5563;
                font-size: 0.95rem;
                font-weight: normal;
                margin-bottom: 20px;
            }
            .upload-box {
                border: 2px dashed #d1d5db;
                border-radius: 16px;
                padding: 30px 10px;
                margin: 20px 0;
                background: #f9fafb;
                cursor: pointer;
            }
            .features {
                display: flex;
                flex-direction: column;
                align-items: start;
                text-align: left;
                font-size: 0.95rem;
                color: #374151;
                gap: 10px;
                margin-bottom: 20px;
            }
            .features span {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .disclaimer {
                font-size: 0.75rem;
                color: #6b7280;
                margin-top: 10px;
            }
            button {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 10px;
                font-size: 1rem;
                cursor: pointer;
                transition: background 0.3s ease;
                width: 100%;
                margin-top: 15px;
            }
            button:hover {
                background-color: #2563eb;
            }
        </style>
    </head>
    <body>
        <div class='card'>
            <h1>DocAI-Помощник</h1>
            <h2>Юридический GPPT-ассистент для анализа и упрощения договоров</h2>

            <form action='/analyze' method='post' enctype='multipart/form-data'>
                <div class='upload-box'>
                    <input type='file' name='file' accept='.pdf,.docx' required />
                    <p>Загрузите договор<br/>(PDF, DOCX)</p>
                </div>

                <div class='features'>
                    <span>🗣️ Объясняет простым языком</span>
                    <span>⚠️ Выделяет риски</span>
                    <span>💡 Даёт советы</span>
                </div>

                <div class='disclaimer'>
                    Это не является юридической консультацией. Используйте как вспомогательный инструмент.
                </div>

                <button type='submit'>Начать анализ</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
