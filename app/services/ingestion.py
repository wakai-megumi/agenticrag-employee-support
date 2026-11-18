from pathlib import Path
from typing import Iterable
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders   import PyPDFLoader, TextLoader
from docx import Document as DocxDocument


supported_file_types = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".docx": DocxDocument,
    ".md": TextLoader,
}


def  load_file (path:Path) -> list[Document]:
    """
    Load a file and return a list of Document objects.
    """
    if not path.exists():
        raise FileNotFoundError(f"File {path} does not exist.")
    
    file_extension = path.suffix.lower()
    if file_extension not in supported_file_types:
        raise ValueError(f"Unsupported file type: {file_extension}")

    loader_class = supported_file_types[file_extension]
    
    if file_extension == ".docx":
        doc = loader_class(path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return [Document(page_content=text)]
    
    loader = loader_class(str(path))
    documents = loader.load()

    
    return documents

def chunk_documents(documents: Iterable[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """
    Chunk documents into smaller pieces.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    return text_splitter.split_documents(list(documents))