from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.exceptions import KnowledgeBaseNotReadyError, LLMProviderError
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import process_chat_request

router = APIRouter()


def get_vector_store(request: Request):
    """Dependency to retrieve vector store from app state."""
    vs = request.app.state.vector_store
    if not vs:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized.")
    return vs


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, vector_store=Depends(get_vector_store)):
    try:
        response = process_chat_request(request, vector_store)
        return response
    except KnowledgeBaseNotReadyError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMProviderError as e:
        # We simplify and just return 502 for provider errors here.
        # Finer grained status codes could map timeout->504, rate_limit->429
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get("/health")
def health_endpoint():
    return {"status": "ok", "service": "company-knowledge-rag"}


@router.get("/ready")
def ready_endpoint(request: Request):
    vs = request.app.state.vector_store
    if not vs:
        return {
            "status": "not_ready",
            "vector_store_initialized": False,
            "collection_exists": False,
            "indexed_chunks": 0,
        }

    try:
        count = vs.count()
        return {
            "status": "ready" if count > 0 else "not_ready",
            "vector_store_initialized": True,
            "collection_exists": True,
            "indexed_chunks": count,
        }
    except Exception:
        return {
            "status": "not_ready",
            "vector_store_initialized": True,
            "collection_exists": False,
            "indexed_chunks": 0,
        }
