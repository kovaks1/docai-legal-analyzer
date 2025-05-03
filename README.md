# DocAI Legal Analyzer

Простое веб-приложение на FastAPI для анализа договоров с помощью OpenAI.

## 🚀 Запуск локально

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Установите переменную окружения с вашим OpenAI API ключом:

**Linux/macOS**:

```bash
export OPENAI_API_KEY=your_key_here
```

**Windows (cmd)**:

```cmd
set OPENAI_API_KEY=your_key_here
```

3. Запустите приложение:

```bash
uvicorn main:app --reload
```

Откройте в браузере: [http://localhost:8000](http://localhost:8000)

## 🌐 Деплой на Railway

- Создайте новый проект и подключите GitHub-репозиторий
- Установите переменную окружения `OPENAI_API_KEY`
