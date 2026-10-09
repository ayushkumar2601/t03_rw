import argparse
import sys
import time

from app.core.config import settings
from app.core.logging import logger
from app.services.ingestion import load_and_split_pdf
from app.services.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest company knowledge base PDF.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the entire collection.")
    args = parser.parse_args()

    start_time = time.time()

    logger.info("[1/5] Validating source PDF...")
    # Validate is done inside load_and_split_pdf
    
    logger.info("[2/5] Extracting page text...")
    logger.info("[3/5] Splitting document into chunks...")
    try:
        chunks, stats = load_and_split_pdf(settings.pdf_path)
    except Exception as e:
        logger.error(f"Ingestion failed during extraction: {e}")
        sys.exit(1)
        
    logger.info("[4/5] Generating embeddings and indexing...")
    try:
        store = VectorStore()
        
        if args.rebuild:
            logger.info("Rebuilding collection as requested...")
            store.clear_collection()
        
        # Check existing chunks to ensure idempotency is logged correctly
        existing_chunks = store.get_by_document_id(stats["document_id"])
        
        # upsert_chunks handles the deletion of old chunks for the same document_id
        indexed_count = store.upsert_chunks(chunks, stats["document_id"])
        stats["chunks_indexed"] = indexed_count
        
        if existing_chunks and len(existing_chunks) == indexed_count and not args.rebuild:
            logger.info("Document unchanged. Replaced identical chunks.")
            
    except Exception as e:
        logger.error(f"Ingestion failed during indexing: {e}")
        sys.exit(1)

    logger.info("[5/5] Validating vector collection...")
    total_in_collection = store.count()
    
    # Smoke test
    smoke_query = "What is the company name?"
    results = store.search(smoke_query, k=1)
    if not results:
        logger.warning("Vector search smoke test returned no results.")
    else:
        logger.info("Vector search smoke test passed.")

    duration = time.time() - start_time
    
    print("\nIngestion completed successfully.")
    print(f"Source filename: {stats['source_filename']}")
    print(f"Total pages: {stats['total_pages']}")
    print(f"Pages containing text: {stats['pages_with_text']} (Empty: {stats['empty_pages']})")
    print(f"Chunks generated: {stats['chunks_generated']}")
    print(f"Chunks indexed: {stats['chunks_indexed']}")
    print(f"Total chunks in collection: {total_in_collection}")
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Collection name: {settings.chroma_collection_name}")
    print(f"Duration: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
