from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger
from app.services.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Starting {settings.app_name} API...")
    try:
        app.state.vector_store = VectorStore()
        logger.info("Vector store initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        app.state.vector_store = None

    yield
    # Shutdown logic
    logger.info("Shutting down API...")


app = FastAPI(
    title=settings.app_name,
    description="API for Company Knowledge Base RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
