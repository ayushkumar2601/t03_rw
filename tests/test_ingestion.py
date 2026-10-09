from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.services.ingestion import load_and_split_pdf, normalize_text, validate_pdf


def test_normalize_text():
    raw_text = "  This   is \n\n\n a test.  "
    expected = "This is \n\n a test."
    assert normalize_text(raw_text) == expected

def test_validate_pdf_missing():
    with pytest.raises(FileNotFoundError):
        validate_pdf("nonexistent.pdf")

def test_validate_pdf_invalid_extension(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    with pytest.raises(ValueError, match="not a PDF"):
        validate_pdf(str(txt_file))

def test_validate_pdf_empty(tmp_path):
    pdf_file = tmp_path / "empty.pdf"
    pdf_file.write_text("")
    with pytest.raises(ValueError, match="empty"):
        validate_pdf(str(pdf_file))

@patch("app.services.ingestion.PyPDFLoader")
def test_load_and_split_pdf_success(mock_loader_class, mock_pdf_path):
    # Setup mock
    mock_loader = MagicMock()
    mock_loader_class.return_value = mock_loader
    mock_loader.load.return_value = [
        Document(page_content="This is page one text.", metadata={"page": 0}),
        Document(page_content="This is page two text.", metadata={"page": 1}),
        Document(page_content="   ", metadata={"page": 2}) # Empty page
    ]
    
    chunks, stats = load_and_split_pdf(mock_pdf_path)
    
    assert stats["total_pages"] == 3
    assert stats["pages_with_text"] == 2
    assert stats["empty_pages"] == 1
    assert len(chunks) > 0
    
    # Check metadata preservation
    for chunk in chunks:
        assert "chunk_id" in chunk.metadata
        assert "document_id" in chunk.metadata
        assert "page" in chunk.metadata
        assert "source" in chunk.metadata
        assert "content_hash" in chunk.metadata
        
@patch("app.services.ingestion.PyPDFLoader")
def test_load_and_split_pdf_no_text(mock_loader_class, mock_pdf_path):
    mock_loader = MagicMock()
    mock_loader_class.return_value = mock_loader
    mock_loader.load.return_value = [
        Document(page_content="   ", metadata={"page": 0}),
    ]
    
    with pytest.raises(ValueError, match="no extractable text"):
        load_and_split_pdf(mock_pdf_path)
