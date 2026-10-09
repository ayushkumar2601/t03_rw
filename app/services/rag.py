import time

from app.core.logging import logger
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RetrievalMetadata,
    SourceReference,
)
from app.services.generation import generate_grounded_answer
from app.services.retrieval import retrieve_context
from app.services.vector_store import VectorStore


def process_chat_request(
    request: ChatRequest, vector_store: VectorStore
) -> ChatResponse:
    """
    Orchestrate the entire RAG pipeline for a given question.
    """
    start_time = time.time()
    question = request.question

    # 1. Retrieval
    retrieval_result = retrieve_context(question, vector_store)
    selected_chunks = retrieval_result["selected_chunks"]

    # Check if retrieval yielded sufficient candidates
    if not selected_chunks:
        return _build_abstain_response(retrieval_result)

    # 2. Generation
    llm_response = generate_grounded_answer(question, selected_chunks)

    # 3. Citation Validation and Sufficiency Evaluation
    if llm_response.abstained:
        return _build_abstain_response(retrieval_result)

    valid_sources = []
    available_chunk_map = {chunk["chunk_id"]: chunk for chunk in selected_chunks}

    for cited_id in llm_response.cited_chunk_ids:
        if cited_id in available_chunk_map:
            chunk = available_chunk_map[cited_id]
            valid_sources.append(
                SourceReference(
                    source=chunk["source"],
                    page=chunk["page"],
                    chunk_id=chunk["chunk_id"],
                    excerpt=chunk["content"][:200] + "..."
                    if len(chunk["content"]) > 200
                    else chunk["content"],
                )
            )
        else:
            logger.warning(
                f"LLM cited an unknown chunk_id: {cited_id}. Rejecting citation."
            )
            # Note: We could retry generation here. For simplicity, we drop invalid citations.

    # If the LLM didn't cite anything valid but gave an answer, we must abstain.
    if not valid_sources:
        logger.error(
            "LLM provided an answer without valid citations. Forcing abstention."
        )
        return _build_abstain_response(retrieval_result)

    duration = time.time() - start_time
    logger.info(
        f"Processed RAG query in {duration:.2f}s. Answered with {len(valid_sources)} citations."
    )

    return ChatResponse(
        answer=llm_response.answer,
        status="answered",
        sources=valid_sources,
        retrieval=RetrievalMetadata(
            chunks_retrieved=retrieval_result["candidates_retrieved"],
            chunks_used=len(valid_sources),  # Used in final answer
        ),
    )


def _build_abstain_response(retrieval_result) -> ChatResponse:
    return ChatResponse(
        answer="I couldn't find sufficient information about that in the provided knowledge-base document.",
        status="insufficient_evidence",
        sources=[],
        retrieval=RetrievalMetadata(
            chunks_retrieved=retrieval_result["candidates_retrieved"], chunks_used=0
        ),
    )
