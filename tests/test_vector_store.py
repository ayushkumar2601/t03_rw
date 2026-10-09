from unittest.mock import patch

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.services.vector_store import VectorStore


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[0.1] * 384 for _ in texts]

    def embed_query(self, text):
        return [0.1] * 384


@pytest.fixture
def fake_vector_store(temp_chroma_dir):
    with patch(
        "app.services.vector_store.get_embedding_model", return_value=FakeEmbeddings()
    ):
        store = VectorStore(persist_dir=temp_chroma_dir, collection_name="test_col")
        yield store


def test_vector_store_initialization(fake_vector_store):
    assert fake_vector_store.count() == 0


def test_upsert_and_retrieve_chunks(fake_vector_store):
    doc_id = "test_doc_1"
    chunks = [
        Document(
            page_content="test chunk 1",
            metadata={"chunk_id": "c1", "document_id": doc_id},
        ),
        Document(
            page_content="test chunk 2",
            metadata={"chunk_id": "c2", "document_id": doc_id},
        ),
    ]

    count = fake_vector_store.upsert_chunks(chunks, doc_id)
    assert count == 2
    assert fake_vector_store.count() == 2

    # Check idempotency
    count2 = fake_vector_store.upsert_chunks(chunks, doc_id)
    assert count2 == 2
    assert fake_vector_store.count() == 2  # Count shouldn't increase

    retrieved_ids = fake_vector_store.get_by_document_id(doc_id)
    assert len(retrieved_ids) == 2
    assert "c1" in retrieved_ids
    assert "c2" in retrieved_ids


def test_search(fake_vector_store):
    doc_id = "test_doc_search"
    chunks = [
        Document(
            page_content="apples and oranges",
            metadata={"chunk_id": "s1", "document_id": doc_id},
        )
    ]
    fake_vector_store.upsert_chunks(chunks, doc_id)

    results = fake_vector_store.search("apples", k=1)
    assert len(results) == 1
    assert results[0][0].page_content == "apples and oranges"


def test_clear_collection(fake_vector_store):
    doc_id = "test_doc_clear"
    chunks = [
        Document(
            page_content="data", metadata={"chunk_id": "d1", "document_id": doc_id}
        )
    ]
    fake_vector_store.upsert_chunks(chunks, doc_id)
    assert fake_vector_store.count() == 1

    fake_vector_store.clear_collection()
    assert fake_vector_store.count() == 0
