from typing import Any, Dict

from app.core.config import settings
from app.core.exceptions import KnowledgeBaseNotReadyError
from app.core.logging import logger
from app.services.vector_store import VectorStore


def retrieve_context(question: str, vector_store: VectorStore) -> Dict[str, Any]:
    """
    Retrieve relevant chunks for a given question.
    Returns candidate chunks, selected chunks, and metadata.
    """
    if vector_store.count() == 0:
        logger.warning("Retrieval attempted but vector store is empty.")
        raise KnowledgeBaseNotReadyError("The knowledge base has not been indexed.")

    # In ChromaDB, similarity_search_with_score returns L2 distance by default (lower is better)
    # The default embeddings used are L2 normalized (HuggingFaceEmbeddings encode_kwargs={'normalize_embeddings': True})
    raw_results = vector_store.search(question, k=settings.retrieval_top_k)

    candidates = []
    selected = []

    # Optional calibration check:
    # If the threshold is 0.0, we just use all top_k. Otherwise filter out high distance.
    # Note: distance metrics might need recalibration if models change.
    threshold = settings.retrieval_min_relevance

    seen_hashes = set()

    for doc, distance in raw_results:
        chunk_info = {
            "chunk_id": doc.metadata.get("chunk_id", "unknown"),
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
            "content": doc.page_content,
            "distance": distance,
        }
        candidates.append(chunk_info)

        # Relevance filtering
        if threshold > 0.0 and distance > threshold:
            logger.debug(
                f"Chunk {chunk_info['chunk_id']} rejected due to distance {distance} > {threshold}"
            )
            continue

        # Deduplication based on content hash
        content_hash = doc.metadata.get("content_hash")
        if content_hash:
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

        selected.append(chunk_info)

    logger.info(
        f"Retrieved {len(candidates)} candidates, selected {len(selected)} for evidence."
    )

    return {
        "question": question,
        "candidates_retrieved": len(candidates),
        "chunks_used": len(selected),
        "selected_chunks": selected,
    }
