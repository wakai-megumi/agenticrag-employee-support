from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header

from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.services.workflow import ask
from app.rag.vectorstore import add_documents_to_vectorstore, get_vectorstore
from app.services.ingestion import load_file, chunk_documents, supported_file_types
from app.services.audit import write_audit_log


router = APIRouter(prefix="/api", tags=["API"])
settings = get_settings()

class ChatRequest(BaseModel):
    question: str = Field(..., example="What is the capital of France?", min_length=2, max_length=500)


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify that the API is running.
    """
    return {"status": "ok", "service_name": settings.app_name}


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        result = ask(request.question)
        write_audit_log(request.question, result["source_used"], result.get("trace", []))
        return {"answer": result["answer"], "source_used": result["source_used"],
                "trace": result.get("trace", []), "citations": result.get("citations", []),
                "rewritten_query": result.get("current_query", request.question)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from  e



@router.post("/ingest")
async def ingest(file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in supported_file_types:
        raise HTTPException(status_code=400, detail=f"Supported: {', '.join(sorted(supported_file_types))}")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / Path(file.filename).name
    dest.write_bytes(await file.read())
    docs = load_file(dest)
    chunks = chunk_documents(docs)
    ids = add_documents_to_vectorstore(chunks)
    return {"message": "Document indexed", "file": dest.name, "chunks": len(chunks), "ids_created": len(ids)}