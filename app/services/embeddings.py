from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings
from app.core.logging import logger

_embedding_instance = None

def get_embedding_model() -> Embeddings:
    """
    Initialize and return the embedding model.
    Loads the model once per process.
    """
    global _embedding_instance
    if _embedding_instance is None:
        model_name = settings.embedding_model
        logger.info(f"Initializing embedding model: {model_name}")
        try:
            _embedding_instance = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}, # Use CPU by default for broader compatibility
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise RuntimeError(f"Embedding model initialization failed: {e}") from e
            
    return _embedding_instance
