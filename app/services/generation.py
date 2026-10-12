import os
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
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


def get_llm() -> BaseChatModel:
    """Initialize and reuse the LLM client (Ollama or Groq)."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    provider = (settings.llm_provider or "ollama").strip().lower()

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama

            _llm_instance = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=settings.llm_temperature,
            )
            logger.info(
                f"Initialized Ollama client (model={settings.ollama_model}, url={settings.ollama_base_url})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise LLMProviderError(f"Failed to initialize Ollama client: {e}") from e
    elif provider == "groq":
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY is not set.")
            raise LLMProviderError(
                "GROQ_API_KEY is not configured. Please set GROQ_API_KEY in your environment or .env file."
            )
        try:
            from langchain_groq import ChatGroq

            _llm_instance = ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.groq_model,
                temperature=settings.llm_temperature,
                timeout=settings.llm_timeout_seconds,
                max_retries=settings.llm_max_retries,
            )
            logger.info(f"Initialized Groq client (model={settings.groq_model})")
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Groq client: {e}") from e
    else:
        raise LLMProviderError(
            f"Unsupported LLM_PROVIDER '{provider}'. Allowed values: 'ollama', 'groq'."
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _invoke_chain_with_retry(chain, inputs: Dict[str, Any]) -> LLMResponse:
    return chain.invoke(inputs)


def generate_grounded_answer(
    question: str, selected_chunks: List[Dict[str, Any]]
) -> LLMResponse:
    """
    Generate an answer using the configured LLM with structured output.
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
        result = _invoke_chain_with_retry(chain, {"context": context_str, "question": question})
        return result
    except LLMProviderError:
        raise
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        raise LLMProviderError(
            f"Failed to generate answer from upstream provider: {e}"
        ) from e
