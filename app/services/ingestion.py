import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import logger


def normalize_text(text: str) -> str:
    """Conservatively normalize text without destroying meaning."""
    # Replace multiple spaces with a single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple blank lines with a single newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Strip leading/trailing whitespace
    return text.strip()

def compute_content_hash(text: str) -> str:
    """Compute a deterministic hash for a given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def validate_pdf(file_path: str) -> None:
    """Validate that the PDF exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source PDF not found at: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    if path.suffix.lower() != '.pdf':
        raise ValueError(f"File is not a PDF: {file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"PDF file is empty: {file_path}")

def load_and_split_pdf(file_path: str) -> Tuple[List[Document], Dict[str, Any]]:
    """
    Load a PDF, normalize its text, and split it into chunks.
    Returns the chunks and a dictionary of ingestion statistics.
    """
    validate_pdf(file_path)
    logger.info(f"Loading PDF from {file_path}")
    
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    total_pages = len(pages)
    if total_pages == 0:
        raise ValueError(f"No pages found in PDF: {file_path}")
    
    extracted_docs = []
    empty_pages = 0
    pages_with_text = 0
    
    source_filename = Path(file_path).name
    
    # Process pages
    for idx, page in enumerate(pages):
        # 1-based page numbers
        page_num = page.metadata.get("page", idx) + 1
        page.metadata["page"] = page_num
        page.metadata["source"] = source_filename
        
        normalized = normalize_text(page.page_content)
        if not normalized:
            empty_pages += 1
            logger.debug(f"Page {page_num} contains no extractable text.")
            continue
            
        pages_with_text += 1
        page.page_content = normalized
        extracted_docs.append(page)
        
    if not extracted_docs:
        raise ValueError("The PDF contains no extractable text. OCR might be required.")
        
    logger.info(f"Extracted text from {pages_with_text}/{total_pages} pages ({empty_pages} empty)")
    
    # Generate full document hash for deterministic document ID
    full_text = "\n\n".join([doc.page_content for doc in extracted_docs])
    document_id = compute_content_hash(full_text)
    
    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = splitter.split_documents(extracted_docs)
    logger.info(f"Generated {len(chunks)} chunks from the document")
    
    # Enhance chunk metadata
    final_chunks = []
    for i, chunk in enumerate(chunks):
        content = chunk.page_content
        if not content.strip():
            continue
            
        content_hash = compute_content_hash(content)
        page_num = chunk.metadata.get("page", 0)
        
        # Deterministic chunk ID
        chunk_id = f"doc_{document_id[:8]}_p{page_num}_c{i}"
        
        chunk.metadata.update({
            "chunk_id": chunk_id,
            "document_id": document_id,
            "chunk_index": i,
            "content_hash": content_hash
        })
        final_chunks.append(chunk)
        
    stats = {
        "source_filename": source_filename,
        "total_pages": total_pages,
        "pages_with_text": pages_with_text,
        "empty_pages": empty_pages,
        "chunks_generated": len(final_chunks),
        "document_id": document_id
    }
    
    return final_chunks, stats
