import os
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging import logger


class LLMResponse(BaseModel):
    answer: str = Field(
        description="The grounded answer to the user's question, or explanation if abstaining."
    )
    abstained: bool = Field(
        description="True if the context does not contain sufficient evidence to answer."
    )
    cited_chunk_ids: List[str] = Field(
        description="List of chunk IDs from the context that support the answer."
    )


_llm_instance = None


def get_llm() -> ChatGroq:
    """Initialize and reuse the Groq LLM client."""
    global _llm_instance
    if _llm_instance is None:
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY is not set.")

        _llm_instance = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    return _llm_instance


def build_context_string(selected_chunks: List[Dict[str, Any]]) -> str:
    """Format chunks into a string for the prompt."""
    context_parts = []
    for chunk in selected_chunks:
        page = chunk.get("page")
        page_str = f" (Page {page})" if page else ""
        context_parts.append(
            f"--- START CHUNK {chunk['chunk_id']} ---\n"
            f"Source: {chunk['source']}{page_str}\n"
            f"{chunk['content']}\n"
            f"--- END CHUNK {chunk['chunk_id']} ---"
        )
    return "\n\n".join(context_parts)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_grounded_answer(
    question: str, selected_chunks: List[Dict[str, Any]]
) -> LLMResponse:
    """
    Generate an answer using Groq with structured output.
    Retries on transient failures.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(LLMResponse)

    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "rag_system.txt"
    )
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{question}")]
    )

    context_str = build_context_string(selected_chunks)

    chain = prompt | structured_llm

    try:
        result = chain.invoke({"context": context_str, "question": question})
        return result
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        raise LLMProviderError(
            f"Failed to generate answer from upstream provider: {e}"
        ) from e
