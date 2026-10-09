from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Company Knowledge Base RAG"
    app_env: str = "development"
    log_level: str = "INFO"

    pdf_path: str = "data/source/knowledge_base.pdf"
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "company_knowledge_base"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 1000
    chunk_overlap: int = 150

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    retrieval_top_k: int = 5
    retrieval_min_relevance: float = 0.0  # Will use threshold later if calibrated
    max_question_length: int = 2000
    llm_temperature: float = 0.0
    llm_max_retries: int = 2
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def validate_chunks(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be strictly less than CHUNK_SIZE")


def get_settings() -> Settings:
    settings = Settings()
    settings.validate_chunks()
    return settings


settings = get_settings()
