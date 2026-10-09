import os
from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings import get_embedding_model


class VectorStore:
    def __init__(
        self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None
    ):
        self.persist_dir = persist_dir or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_model = get_embedding_model()
        self.db = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize ChromaDB with persistence."""
        os.makedirs(self.persist_dir, exist_ok=True)
        try:
            self.db = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_dir,
                collection_metadata={"embedding_model": settings.embedding_model},
            )
            # Verify compatibility
            actual_model = self.db._collection.metadata.get("embedding_model")
            if actual_model and actual_model != settings.embedding_model:
                logger.error(
                    f"Collection uses incompatible embedding model: {actual_model}"
                )
                raise ValueError(
                    f"Incompatible embedding model in collection. Expected {settings.embedding_model}, found {actual_model}."
                )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def count(self) -> int:
        """Return the total number of chunks in the collection."""
        if not self.db:
            return 0
        return self.db._collection.count()

    def get_by_document_id(self, document_id: str) -> List[str]:
        """Return all chunk IDs belonging to a specific document."""
        if not self.db:
            return []
        result = self.db.get(where={"document_id": document_id})
        return result.get("ids", [])

    def delete_by_document_id(self, document_id: str):
        """Delete all chunks belonging to a specific document."""
        ids_to_delete = self.get_by_document_id(document_id)
        if ids_to_delete:
            self.db.delete(ids=ids_to_delete)
            logger.info(
                f"Deleted {len(ids_to_delete)} old chunks for document {document_id}"
            )

    def upsert_chunks(self, chunks: List[Document], document_id: str) -> int:
        """
        Idempotent insertion of chunks for a document.
        Removes any existing chunks for this document first.
        """
        if not chunks:
            return 0

        self.delete_by_document_id(document_id)

        ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        self.db.add_documents(documents=chunks, ids=ids)
        return len(chunks)

    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Perform similarity search.
        Returns chunks and their distance scores.
        """
        if not self.db:
            return []

        # similarity_search_with_score returns lower score for better matches (distance)
        results = self.db.similarity_search_with_score(query, k=k)
        return results

    def clear_collection(self):
        """Delete the entire collection."""
        if self.db:
            try:
                self.db.delete_collection()
                logger.info(f"Deleted vector store collection {self.collection_name}")
                self.db = None
                self._initialize_db()
            except Exception as e:
                logger.error(f"Failed to clear vector store: {e}")
                raise
