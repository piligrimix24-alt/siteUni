# openrouter_server.py
import os
import glob
import re
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ===== НАСТРОЙКИ =====
OPENROUTER_API_KEY = "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"

DOCS_DIR = r"C:\siteUni\docs"
COLLECTION_NAME = "my_plants_knowledge_base"

PRETTY_NAMES = {
    "plants/mint.md": "Мята — уход и выращивание",
    "plants/basil.md": "Базилик — уход и выращивание",
    "plants/parsley.md": "Петрушка — уход и выращивание",
    "plants/dill.md": "Укроп — уход и выращивание",
    "plants/salad.md": "Салат — уход и выращивание",
    "plants/chives.md": "Зелёный лук — уход и выращивание",
    "plants/microgreens.md": "Микрозелень — уход и выращивание",
    "plants/tomatoes.md": "Помидоры черри — уход и выращивание",
    "plants/peppers.md": "Перец — уход и выращивание",
    "plants/radish.md": "Редис — уход и выращивание",
    "care/greens.md": "Гайд по уходу за зеленью",
    "care/tomatoes.md": "Гайд по томатам",
    "care/peppers.md": "Гайд по перцам",
    "care/radish.md": "Гайд по редису",
    "care/problems.md": "Проблемы и решения",
    "recipes/greens.md": "Рецепты с зеленью",
    "recipes/tomatoes.md": "Рецепты с помидорами",
    "recipes/peppers.md": "Рецепты с перцами",
    "recipes/radish.md": "Рецепты с редисом",
}

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

print("Запуск сервера...")

# Проверка Ollama
import subprocess
try:
    subprocess.run(["ollama", "list"], capture_output=True, check=True)
except:
    print("Ошибка: Ollama не запущена!")
    exit(1)

# База данных
chroma_client = chromadb.PersistentClient(path="./chroma_data")
embedder = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedder
)

# Индексация (исключаем notUsed)
print("Загрузка статей...")
all_md_files = glob.glob(os.path.join(DOCS_DIR, "**/*.md"), recursive=True)
exclude = ["index.md", "api-examples.md", "markdown-examples.md"]
md_files = [f for f in all_md_files if os.path.basename(f) not in exclude and "notUsed" not in f]

existing = collection.get()['metadatas'] if collection.count() > 0 else []
existing_sources = [m['source'] for m in existing if m] if existing else []

for file_path in md_files:
    source_id = file_path.replace(DOCS_DIR, "").lstrip("\\/").replace("\\", "/")
    if source_id in existing_sources:
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    collection.add(
        ids=[source_id],
        documents=[content],
        metadatas=[{"source": source_id}]
    )
    print(f"  Добавлен: {source_id}")

print(f"База знаний готова. Всего статей: {collection.count()}")

# ===== WEB-СЕРВЕР =====
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

def clean_markdown(text):
    """Убирает Markdown-разметку: **жирный**, *курсив*, __подчеркивание__"""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    return text

@app.get("/health")
async def health():
    return {"status": "ok", "documents_in_db": collection.count()}

@app.post("/ask")
async def ask(request: QuestionRequest):
    user_question = request.question
    print(f"Вопрос: {user_question}")
    
    results = collection.query(query_texts=[user_question], n_results=4)
    
    if not results['documents'] or not results['documents'][0]:
        return {"answer": "Не нашёл информации."}
    
    context_parts = []
    sources = []
    for i, doc in enumerate(results['documents'][0]):
        source = results['metadatas'][0][i]['source']
        if "notUsed" in source:
            continue
        sources.append(source)
        context_parts.append(f"--- Источник: {source} ---\n{doc[:2000]}")
    
    if not sources:
        return {"answer": "Информация найдена, но она находится в черновиках. Опубликуйте статьи."}
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""Ты - AI-ассистент сайта "Сад на подоконнике". Отвечай ТОЛЬКО на русском, используй ТОЛЬКО контекст. 
НЕ используй Markdown-разметку (не пиши **жирный**, *курсив*). Пиши только обычный текст.

КОНТЕКСТ:
{context}

ВОПРОС: {user_question}

ОТВЕТ:
"""
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000
        )
        answer = response.choices[0].message.content
        if answer is None:
            answer = "Не удалось получить ответ."
        answer = clean_markdown(answer)
        
                # Формируем ссылки
        clean_links = []
        for source in sources:
            pretty_name = PRETTY_NAMES.get(source, source.replace(".md", "").replace("/", " → "))
        #     # Убираем .md, добавляем .html
        #     link = source.replace(".md", ".html")
        #     # Полная ссылка
        #     full_url = f"http://localhost:5173/{link}"
        #     # Оборачиваем в <a> тег
        #     clean_links.append(f'<a href="{full_url}">{pretty_name}</a>')
            clean_links.append(pretty_name)
        
        sources_html = "Источники: \n" + ", \n".join(clean_links)
        # Объединяем
        final_answer = f"{answer}\n\n{sources_html}"
        
        return {"answer": final_answer}
        
    except Exception as e:
        return {"answer": f"Ошибка: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)