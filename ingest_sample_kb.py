from pathlib import Path
from app.services.ingestion import load_file, chunk_documents
from app.rag.vectorstore import add_documents_to_vectorstore, get_retriever
from app.core.config import get_settings


settings  =     get_settings()
folder = Path(settings.sample_kb_dir)
files = [p for p in folder.iterdir() if p.is_file()]

all_documents = []
for file in files:
    try:
        documents = load_file(file)
        all_documents.extend(documents)
    except Exception as e:
        print(f"Error loading file {file}: {e}")

    chunked_documents = chunk_documents(documents, chunk_size=1000, chunk_overlap=200)
    ids = add_documents_to_vectorstore(chunked_documents)
    print(f"Added {len(chunked_documents)} documents from {file} to vectorstore with IDs: {ids}")



