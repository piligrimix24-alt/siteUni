import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

# Настройки
MD_DIR = r"C:\siteUni\docs"
CHROMA_DIR = r"C:\siteUni\backend\chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def load_markdown_files(directory):
    """Загружает все .md файлы из папки и подпапок"""
    documents = []
    md_files = glob.glob(os.path.join(directory, "**/*.md"), recursive=True)
    
    exclude = ["index.md", "api-examples.md", "markdown-examples.md"]
    md_files = [f for f in md_files if os.path.basename(f) not in exclude]
    
    print(f"Найдено {len(md_files)} файлов:")
    for file_path in md_files:
        print(f"  - {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            rel_path = file_path.replace(MD_DIR, "").lstrip("\\/")
            documents.append({
                "page_content": content,
                "metadata": {"source": rel_path}
            })
        except Exception as e:
            print(f"Ошибка чтения {file_path}: {e}")
    
    return documents

def create_and_save_db(documents, persist_dir):
    """Создаёт векторную базу из документов"""
    print("\nНастройка эмбеддера Ollama...")
    import subprocess
    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True)
    except:
        print("Ollama не запущена! Запустите Ollama из меню Пуск и повторите.")
        return None
    
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    
    docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in documents]
    
    chunks = text_splitter.split_documents(docs)
    print(f"Создано {len(chunks)} фрагментов из {len(documents)} файлов")
    
    print("Создание векторной базы данных...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    print(f"База данных сохранена в {persist_dir}")
    
    return vectorstore

if __name__ == "__main__":
    print("=== ИНДЕКСАЦИЯ СТАТЕЙ ДЛЯ RAG ===\n")
    documents = load_markdown_files(MD_DIR)
    if documents:
        vectorstore = create_and_save_db(documents, CHROMA_DIR)
        if vectorstore:
            print("\nГотово! База знаний создана.")
            print(f"   Количество документов в базе: {vectorstore._collection.count()}")
    else:
        print("Не найдено ни одного .md файла. Проверьте путь.")