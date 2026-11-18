from pathlib import Path
from app.services.ingestion import load_file, chunk_documents




docs = load_file(Path("data/sample_kb/company_hr_handbook.md"))
chunked_docs = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)
print(f"Number of chunked documents: {len(chunked_docs)}")