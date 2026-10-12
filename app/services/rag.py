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

    # Handle common conversational pleasantries and greetings
    norm_q = question.strip().lower().rstrip(".!?,")
    conversational_answers = {
        "ok": "Understood! Feel free to ask any questions about Agarwal Constructions, our founder, projects, history, or policies.",
        "okay": "Understood! Feel free to ask any questions about Agarwal Constructions, our founder, projects, history, or policies.",
        "k": "Understood! Feel free to ask any questions about Agarwal Constructions.",
        "fine": "Glad to hear! How can I assist you with Agarwal Constructions today?",
        "sure": "Great! Feel free to ask any question about the company.",
        "cool": "Happy to help! What would you like to know about Agarwal Constructions?",
        "great": "Glad to hear! Feel free to ask any question about our projects or company profile.",
        "got it": "Understood! Feel free to ask anything else about Agarwal Constructions.",
        "understood": "Perfect! Let me know if you need any other information from the knowledge base.",
        "sounds good": "Great! Let me know what you'd like to explore next.",
        "hi": "Hello! I am the Agarwal Constructions AI Assistant. Ask me anything about our company's history, projects, leadership, or operations.",
        "hello": "Hello! I am the Agarwal Constructions AI Assistant. Ask me anything about our company's history, projects, leadership, or operations.",
        "hey": "Hey there! I am here to answer any questions about Agarwal Constructions.",
        "thanks": "You're very welcome! Let me know if you need any other details.",
        "thank you": "You're very welcome! Let me know if you need any other details.",
        "thx": "You're welcome! Let me know if you have any more questions.",
        "who are you": "I am the Agarwal Constructions Knowledge Base AI. I provide accurate, verified information about the company based on our official documentation.",
        "what can you do": "I can answer questions about Agarwal Constructions, including our founder Rajesh Agarwal, founding story, project portfolio, delivered square footage, head office contacts, and company policies.",
    }
    if norm_q in conversational_answers:
        return ChatResponse(
            answer=conversational_answers[norm_q],
            status="answered",
            sources=[],
            retrieval=RetrievalMetadata(chunks_retrieved=0, chunks_used=0),
        )

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

    cleaned_answer = clean_answer_text(llm_response.answer)

    return ChatResponse(
        answer=cleaned_answer,
        status="answered",
        sources=valid_sources,
        retrieval=RetrievalMetadata(
            chunks_retrieved=retrieval_result["candidates_retrieved"],
            chunks_used=len(valid_sources),  # Used in final answer
        ),
    )


def clean_answer_text(text: str) -> str:
    """Sanitize answer text to eliminate accidental single-word line breaks and ensure fluid paragraphs."""
    if not text:
        return text
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) > 4:
        avg_words = sum(len(l.split()) for l in lines) / len(lines)
        if avg_words < 2.5:
            text = " ".join(lines)
    import re
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_abstain_response(retrieval_result) -> ChatResponse:
    return ChatResponse(
        answer="I couldn't find sufficient information about that in the provided knowledge-base document.",
        status="insufficient_evidence",
        sources=[],
        retrieval=RetrievalMetadata(
            chunks_retrieved=retrieval_result["candidates_retrieved"], chunks_used=0
        ),
    )
