from unittest.mock import MagicMock, patch

from app.schemas.chat import ChatRequest
from app.services.generation import LLMResponse
from app.services.rag import process_chat_request


def test_process_chat_request_abstain_no_chunks():
    request = ChatRequest(question="test")
    mock_vs = MagicMock()
    mock_vs.count.return_value = 1
    mock_vs.search.return_value = []

    response = process_chat_request(request, mock_vs)
    assert response.status == "insufficient_evidence"
    assert len(response.sources) == 0


@patch("app.services.rag.generate_grounded_answer")
@patch("app.services.rag.retrieve_context")
def test_process_chat_request_llm_abstains(mock_retrieve, mock_generate):
    mock_retrieve.return_value = {
        "candidates_retrieved": 1,
        "selected_chunks": [
            {"chunk_id": "c1", "source": "src", "page": 1, "content": "text"}
        ],
    }

    mock_generate.return_value = LLMResponse(
        answer="I don't know.", abstained=True, cited_chunk_ids=[]
    )

    mock_vs = MagicMock()
    response = process_chat_request(ChatRequest(question="test"), mock_vs)

    assert response.status == "insufficient_evidence"
    assert response.retrieval.chunks_used == 0


@patch("app.services.rag.generate_grounded_answer")
@patch("app.services.rag.retrieve_context")
def test_process_chat_request_valid_citation(mock_retrieve, mock_generate):
    mock_retrieve.return_value = {
        "candidates_retrieved": 1,
        "selected_chunks": [
            {"chunk_id": "c1", "source": "src", "page": 1, "content": "text"}
        ],
    }

    mock_generate.return_value = LLMResponse(
        answer="Valid answer.", abstained=False, cited_chunk_ids=["c1"]
    )

    mock_vs = MagicMock()
    response = process_chat_request(ChatRequest(question="test"), mock_vs)

    assert response.status == "answered"
    assert len(response.sources) == 1
    assert response.sources[0].chunk_id == "c1"


@patch("app.services.rag.generate_grounded_answer")
@patch("app.services.rag.retrieve_context")
def test_process_chat_request_invalid_citation_rejected(mock_retrieve, mock_generate):
    mock_retrieve.return_value = {
        "candidates_retrieved": 1,
        "selected_chunks": [
            {"chunk_id": "c1", "source": "src", "page": 1, "content": "text"}
        ],
    }

    # LLM cited a chunk that wasn't provided
    mock_generate.return_value = LLMResponse(
        answer="Fabricated answer.", abstained=False, cited_chunk_ids=["fabricated_c2"]
    )

    mock_vs = MagicMock()
    response = process_chat_request(ChatRequest(question="test"), mock_vs)

    assert response.status == "insufficient_evidence"
    assert len(response.sources) == 0
