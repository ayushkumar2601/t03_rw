from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class ChatRequest(BaseModel):
    question: str = Field(
        ..., description="The user's question about the knowledge base."
    )

    @field_validator("question")
    def validate_question(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty or just whitespace.")
        if len(v) > settings.max_question_length:
            raise ValueError(
                f"Question exceeds maximum length of {settings.max_question_length} characters."
            )
        return v


class SourceReference(BaseModel):
    source: str
    page: Optional[int]
    chunk_id: str
    excerpt: str


class RetrievalMetadata(BaseModel):
    chunks_retrieved: int
    chunks_used: int


class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "insufficient_evidence"]
    sources: List[SourceReference]
    retrieval: RetrievalMetadata
