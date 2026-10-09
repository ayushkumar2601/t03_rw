from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_vector_store():
    vs = MagicMock()
    app.state.vector_store = vs
    yield vs
    app.state.vector_store = None


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "company-knowledge-rag"}


def test_ready_empty(mock_vector_store):
    mock_vector_store.count.return_value = 0
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "not_ready"


def test_ready_populated(mock_vector_store):
    mock_vector_store.count.return_value = 100
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_chat_missing_question(mock_vector_store):
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_empty_question(mock_vector_store):
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 422


def test_chat_db_not_ready():
    app.state.vector_store = None
    response = client.post("/chat", json={"question": "test"})
    assert response.status_code == 503


@patch("app.api.routes.process_chat_request")
def test_chat_success(mock_process, mock_vector_store):
    mock_process.return_value = {
        "answer": "test answer",
        "status": "answered",
        "sources": [],
        "retrieval": {"chunks_retrieved": 1, "chunks_used": 1},
    }

    response = client.post("/chat", json={"question": "What is the policy?"})
    assert response.status_code == 200
    assert response.json()["status"] == "answered"


@patch("app.api.routes.process_chat_request")
def test_chat_llm_provider_error(mock_process, mock_vector_store):
    from app.core.exceptions import LLMProviderError

    mock_process.side_effect = LLMProviderError("Upstream error")

    response = client.post("/chat", json={"question": "test"})
    assert response.status_code == 502
