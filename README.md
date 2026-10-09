# Company Knowledge Base RAG Chatbot (Phase 1)

This project implements Phase 1 of the Company Knowledge Base RAG Chatbot. 
In this phase, we have established the foundational data ingestion and vector storage pipeline.

## Architecture Overview (Phase 1)
- **Document Loading**: `PyPDFLoader` is used to parse the company knowledge base PDF and extract text with page metadata.
- **Text Processing**: Basic normalization is applied to preserve paragraph structures, followed by recursive chunk splitting via `RecursiveCharacterTextSplitter`.
- **Embeddings**: `HuggingFaceEmbeddings` utilizing `sentence-transformers/all-MiniLM-L6-v2`. (The model will be downloaded locally upon first run).
- **Vector Storage**: `Chroma` database persists embeddings locally into a specific directory, supporting idempotent updates based on content hashes.

## Prerequisites
- Python 3.11
- Virtual environment

## Setup

1. **Virtual Environment & Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy the example environment variables:
   ```bash
   cp .env.example .env
   ```
   You can adjust values in `.env` like chunk size or database paths as needed.

3. **PDF Placement**:
   Place the provided company knowledge base PDF into the expected directory:
   ```bash
   mkdir -p data/source
   # Move your PDF to data/source/knowledge_base.pdf
   ```

## Usage

### Ingestion Command

To run the pipeline and ingest the PDF:

```bash
python -m scripts.ingest
```

This process will:
1. Validate the PDF.
2. Extract text and page metadata.
3. Split the text into meaningful overlapping chunks.
4. Generate embeddings (the embedding model is loaded locally).
5. Upsert the chunks into ChromaDB (idempotent, won't duplicate on rerun).
6. Verify indexing with a smoke test.

To completely rebuild the collection (delete all previous embeddings and start fresh):

```bash
python -m scripts.ingest --rebuild
```

## Testing

Run tests to verify ingestion and vector store mechanics (does not require external APIs or internet access after deps are installed):

```bash
pytest
```

## Current Limitations (Phase 1)
- This phase focuses solely on data ingestion and vector storage.
- The FastAPI endpoints and Groq LLM integration (Phase 2) are not yet implemented.
- The `knowledge_base.pdf` provided for the assignment must contain extractable text (OCR is not supported yet).
- Embedding models run on the CPU by default for maximum compatibility across machines.
