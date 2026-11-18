// code for storing and retrieving documents from a vector store

import time
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPineconeStore
from app.core.config import get_settings

settings = get_settings()

_embeddings = None
_vectorstore = None

EMBEDDINGS_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "Text-embedding-ada-002": 1536,
    "all-minilm-l6-v2": 384,
}


def  get_embedding_dimension(model_name: str|None = None) -> int:
    """
    Get the embedding dimension for a given model name.
    """
    if not model_name:
        raise ValueError("embedding Model name must be provided.")
    normalized_model_name = model_name.lower()
    if normalized_model_name not in EMBEDDINGS_DIMENSIONS:
        raise ValueError(f"Unsupported model name: {model_name}")
    return EMBEDDINGS_DIMENSIONS[normalized_model_name]


def get_embeddings():
    
    global _embeddings
    if _embeddings is None:
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key must be provided in settings.")
        _embeddings = OpenAIEmbeddings(
         model =   settings.embedding_model,
         api_key = settings.openai_api_key,)

    return _embeddings


def ensure_index():
    if not settings.pinecone_api_key:
        
        raise ValueError("Pinecone API key and environment must be provided in settings.")

    desired_dimension = get_embedding_dimension(settings.embedding_model)
    pc = Pinecone(api_key=settings.pinecone_api_key, environment="us-east1-gcp")
    names=  [index.name for index in pc.list_indexes()]

    
    if settings.pinecone_index_name in names:
        index_info = pc.describe_index(settings.pinecone_index_name)
        current_dimension = index_info.dimension
        if current_dimension is None and isinstance(index_info, dict):
            current_dimension = index_info.get("dimension")

        if current_dimension is None and current_dimension != desired_dimension:
            pc.delete_index(settings.pinecone_index_name)
            while True:
                names = [index.name for index in pc.list_indexes()]
                if settings.pinecone_index_name not in names:
                    break
                print("Waiting for Pinecone index to be deleted...")
                time.sleep(3)

    if settings.pinecone_index_name not in names:
            print(f"Creating Pinecone index: {settings.pinecone_index_name} with dimension {desired_dimension}")
            pc.create_index(
                name=settings.pinecone_index_name,
                dimension=desired_dimension,
                metric="cosine",
                serverless=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            # Wait for the index to be ready
            while True:
                
                index_info = pc.describe_index(settings.pinecone_index_name)
                if index_info.status["ready"]:
                    break
                print("Waiting for Pinecone index to be ready...")
                time.sleep(3)
    
    return pc.Index(settings.pinecone_index_name)


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        index = ensure_index()
        embeddings = get_embeddings()
        _vectorstore = LangchainPineconeStore(
            index=index,
            embedding=embeddings,
            namespace=settings.pinecone_namespace,
        )
    return _vectorstore

def get_retriever(top_k: int | None = None):
    vectorstore = get_vectorstore()
    if top_k is None:
        top_k = settings.top_k
    return vectorstore.as_retriever(search_kwargs={"k": top_k})

def add_documents_to_vectorstore(documents):
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents)