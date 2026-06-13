# modern_server.py
import os
import glob
import chromadb
from chromadb.utils import embedding_functions
import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

#  НАСТРОЙКИ 
# Путь к твоим статьям
DOCS_DIR = r"C:\siteUni\docs"
# Название коллекции в нашей базе данных
COLLECTION_NAME = "my_plants_knowledge_base"
# Модель для поиска смыслов (embedding)
EMBEDDING_MODEL = "nomic-embed-text"
# Модель для генерации ответов (LLM)
LLM_MODEL = "llama3.2:3b"

#  1. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (ChromaDB) 
print(" Запуск сервера...")
# Подключаемся к ChromaDB (она будет хранить файлы в папке './chroma_data')
chroma_client = chromadb.PersistentClient(path="./chroma_data")
# Настраиваем функцию, которая будет создавать эмбеддинги через Ollama
embedder = embedding_functions.OllamaEmbeddingFunction(
    model_name=EMBEDDING_MODEL,
    url="http://localhost:11434/api/embeddings" # Стандартный адрес Ollama
)

# Получаем или создаем коллекцию (как таблицу в базе данных)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedder
)

#  2. ЗАГРУЗКА СТАТЕЙ В БАЗУ (выполнится один раз при запуске)
print("📚 Проверка и загрузка статей в базу знаний...")

# Находим все .md файлы
all_md_files = glob.glob(os.path.join(DOCS_DIR, "**/*.md"), recursive=True)
# Исключаем служебные файлы, если они есть
exclude_files = ["index.md", "api-examples.md", "markdown-examples.md"]
md_files = [f for f in all_md_files if os.path.basename(f) not in exclude_files]

# Узнаем, какие файлы уже есть в базе, чтобы не добавлять их повторно
existing_metadata = collection.get()['metadatas'] if collection.count() > 0 else []
existing_sources = [meta['source'] for meta in existing_metadata if meta] if existing_metadata else []

# Счетчик добавленных файлов
added_count = 0
for file_path in md_files:
    # Создаем относительный путь, который станет ID документа
    source_id = file_path.replace(DOCS_DIR, "").lstrip("\\/").replace("\\", "/")
    
    # Если файл уже в базе, пропускаем его
    if source_id in existing_sources:
        continue
        
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем документ в коллекцию ChromaDB
    # id — уникальный идентификатор, documents — сам текст, metadatas — дополнительная информация
    collection.add(
        ids=[source_id],
        documents=[content],
        metadatas=[{"source": source_id}]
    )
    added_count += 1
    print(f"  ✅ Добавлен: {source_id}")

if added_count > 0:
    print(f"✨ База знаний обновлена. Добавлено {added_count} новых статей.")
else:
    print(f"✅ База знаний актуальна. Всего статей в базе: {collection.count()}")

#  3. СОЗДАНИЕ WEB-СЕРВЕРА (FastAPI) 
app = FastAPI(title="AI Ассистент для Сада на подоконнике")

# Разрешаем твоему сайту общаться с сервером
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель для данных, которые придут с сайта
class QuestionRequest(BaseModel):
    question: str

#  4. ФУНКЦИЯ ПОИСКА (RAG) 
@app.post("/ask")
async def ask(request: QuestionRequest):
    """
    Этот эндпоинт получает вопрос, ищет похожие статьи в базе данных,
    и просит LLM сформировать ответ на их основе.
    """
    user_question = request.question
    print(f"❓ Вопрос: {user_question}")  # Отлично для отладки в терминале
    
    # Шаг 1: Ищем в ChromaDB 3 самых похожих отрывка из твоих статей
    try:
        results = collection.query(
            query_texts=[user_question],
            n_results=3  # Возвращаем топ-3 релевантных куска
        )
    except Exception as e:
        print(f"Ошибка при поиске в базе: {e}")
        return {"answer": "Извините, произошла ошибка при поиске информации в базе знаний."}
    
    # Шаг 2: Форматируем найденные статьи в понятный для ИИ вид
    context_parts = []
    sources = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            source = results['metadatas'][0][i]['source']
            sources.append(source)
            # Ограничиваем длину текста, чтобы не перегружать модель
            context_parts.append(f"Из статьи '{source}':\n{doc[:1000]}...")
    
    if not context_parts:
        return {"answer": "Не нашел подходящей информации по вашему вопросу в моей базе знаний."}
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Шаг 3: Создаем "промпт" — инструкцию для ИИ
    prompt = f"""Ты — полезный AI-ассистент базы знаний «Сад на подоконнике» на русском языке.

ВАЖНО: Отвечай ТОЛЬКО на русском языке! Даже если вопрос задан на другом языке — отвечай по-русски.

Используй информацию только из контекста ниже.
Если точного ответа нет, дай общий совет, но честно скажи, что информации мало.
Обязательно укажи, из какой статьи информация.

КОНТЕКСТ:
{context}

ВОПРОС ПО-РУССКИ: {user_question}

ОТВЕТ ПО-РУССКИ (с указанием источника):
"""
    
    # Шаг 4: Отправляем запрос в локальную LLM (через Ollama)
    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        answer = response['message']['content']
        # Добавим в ответ список источников для наглядности
        sources_list = "\n\n📚 **Источники:** " + ", ".join(sources)
        final_answer = answer + sources_list
        return {"answer": final_answer}
    except Exception as e:
        print(f"Ошибка при обращении к Ollama: {e}")
        return {"answer": f"Ошибка при получении ответа от модели. Убедитесь, что Ollama запущена (команда `ollama serve`)."}

# Точка для проверки, что сервер жив
@app.get("/health")
async def health():
    return {"status": "ok", "documents_in_db": collection.count()}

#  5. ЗАПУСК СЕРВЕРА 
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🌱 Сервер готов к работе!")
    print(f"📚 В базе данных: {collection.count()} статей")
    print(f"🌐 Сайт может обращаться к серверу по адресу: http://localhost:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)