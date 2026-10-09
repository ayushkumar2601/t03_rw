from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from app.core.exceptions import KnowledgeBaseNotReadyError
from app.services.retrieval import retrieve_context


def test_retrieve_context_empty_db():
    mock_vs = MagicMock()
    mock_vs.count.return_value = 0
    with pytest.raises(KnowledgeBaseNotReadyError):
        retrieve_context("test question", mock_vs)


def test_retrieve_context_success():
    mock_vs = MagicMock()
    mock_vs.count.return_value = 5
    mock_vs.search.return_value = [
        (
            Document(
                page_content="content1",
                metadata={"chunk_id": "c1", "source": "src1", "page": 1},
            ),
            0.1,
        ),
        (
            Document(
                page_content="content2",
                metadata={"chunk_id": "c2", "source": "src1", "page": 2},
            ),
            0.2,
        ),
    ]

    result = retrieve_context("test question", mock_vs)
    assert result["candidates_retrieved"] == 2
    assert result["chunks_used"] == 2
    assert len(result["selected_chunks"]) == 2
    assert result["selected_chunks"][0]["chunk_id"] == "c1"


def test_retrieve_context_deduplication():
    mock_vs = MagicMock()
    mock_vs.count.return_value = 5
    # Both have the same content hash
    mock_vs.search.return_value = [
        (
            Document(
                page_content="content1",
                metadata={"chunk_id": "c1", "content_hash": "hash1"},
            ),
            0.1,
        ),
        (
            Document(
                page_content="content1",
                metadata={"chunk_id": "c1_dup", "content_hash": "hash1"},
            ),
            0.2,
        ),
    ]

    result = retrieve_context("test question", mock_vs)
    assert result["candidates_retrieved"] == 2
    assert result["chunks_used"] == 1
    assert result["selected_chunks"][0]["chunk_id"] == "c1"
