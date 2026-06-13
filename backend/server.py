# modern_server.py
import os
import glob
import chromadb
from chromadb.utils import embedding_functions
import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# НАСТРОЙКИ 
# Путь к статьям
DOCS_DIR = r"C:\siteUni\docs"
# Название коллекции в базе данных
COLLECTION_NAME = "my_plants_knowledge_base"
# embedding
EMBEDDING_MODEL = "nomic-embed-text"
# Модель для генерации ответов
LLM_MODEL = "qwen2:1.5b"

#  ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
print(" Запуск сервера...")
chroma_client = chromadb.PersistentClient(path="./chroma_data")
embedder = embedding_functions.OllamaEmbeddingFunction(
    model_name=EMBEDDING_MODEL,
    url="http://localhost:11434/api/embeddings"
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedder
)

# ЗАГРУЗКА СТАТЕЙ В БАЗУ
print(" Проверка и загрузка статей в базу знаний...")

all_md_files = glob.glob(os.path.join(DOCS_DIR, "**/*.md"), recursive=True)

exclude_files = ["index.md", "api-examples.md", "markdown-examples.md"]
md_files = [f for f in all_md_files if os.path.basename(f) not in exclude_files]

existing_metadata = collection.get()['metadatas'] if collection.count() > 0 else []
existing_sources = [meta['source'] for meta in existing_metadata if meta] if existing_metadata else []

# Счетчик добавленных файлов
added_count = 0
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
    added_count += 1
    print(f"  Добавлен: {source_id}")

if added_count > 0:
    print(f" База знаний обновлена. Добавлено {added_count} новых статей.")
else:
    print(f" База знаний актуальна. Всего статей в базе: {collection.count()}")

#  СОЗДАНИЕ WEB-СЕРВЕРА
app = FastAPI(title="AI Ассистент для Сада на подоконнике")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(request: QuestionRequest):
    """Основной эндпоинт для вопросов"""
    user_question = request.question
    print(f"Вопрос: {user_question}")
    
    try:
        results = collection.query(
            query_texts=[user_question],
            n_results=3
        )
    except Exception as e:
        print(f"Ошибка при поиске в базе: {e}")
        return {"answer": "Извините, произошла ошибка при поиске информации в базе знаний."}
    
    context_parts = []
    sources = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            source = results['metadatas'][0][i]['source']
            sources.append(source)
            context_parts.append(f"Из статьи '{source}':\n{doc[:1000]}...")
    
    if not context_parts:
        return {"answer": "Не нашел подходящей информации по вашему вопросу в моей базе знаний."}
    
    context = "\n\n---\n\n".join(context_parts)
    
    prompt = f"""Ты — полезный AI-ассистент базы знаний «Сад на подоконнике».
ВАЖНО:
1. Отвечай ТОЛЬКО на русском языке.
2. Используй информацию ТОЛЬКО из контекста ниже.
3. Когда ссылаешься на источник, пиши ПОЛНОЕ ИМЯ ФАЙЛА, например: `plants/mint.md` или `care/greens.md`.
4. Не пиши "Из статьи 'plants/mint.md' упоминается", а пиши естественно, а в конце перечисли источники.
КОНТЕКСТ:
{context}
ВОПРОС: {user_question}
ОТВЕТ (на русском, естественным языком, с перечислением источников в конце в формате « Источники: plants/mint.md, care/greens.md»):
"""

    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {'role': 'user', 'content': prompt},
        ])
        answer = response['message']['content']
        
        import re
        def make_link(match):
            filename = match.group(1)
            clean_name = filename.replace("docs/", "")
            return f'<a href="/{clean_name}">{filename}</a>'
        linked_answer = re.sub(r'([\w\/\-]+\.md)', make_link, answer)

        linked_answer = f'<div class="rag-answer">{linked_answer}</div>'
        
        return {"answer": linked_answer}
    except Exception as e:
        print(f"Ошибка при обращении к Ollama: {e}")
        return {"answer": f"Ошибка при получении ответа от модели. Убедитесь, что Ollama запущена."}

@app.get("/health")
async def health():
    return {"status": "ok", "documents_in_db": collection.count()}

#  ЗАПУСК СЕРВЕРА 
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print(" Сервер готов к работе!")
    print(f" В базе данных: {collection.count()} статей")
    print(f" Сайт может обращаться к серверу по адресу: http://localhost:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)