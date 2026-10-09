import tempfile

import pytest


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Override environment variables for testing."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CHUNK_SIZE", "100")
    monkeypatch.setenv("CHUNK_OVERLAP", "20")

@pytest.fixture
def temp_chroma_dir():
    """Provide a temporary directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a temporary dummy PDF file."""
    # Note: creating a real PDF programmatically is complex, 
    # we will rely on mocking PyPDFLoader or using a small synthetic valid PDF if needed.
    pdf_file = tmp_path / "dummy.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n%EOF\n")
    return str(pdf_file)
