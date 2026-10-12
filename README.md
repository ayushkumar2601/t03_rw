# Company Knowledge Base RAG Chatbot

This project implements a high-precision Retrieval-Augmented Generation (RAG) Chatbot built with FastAPI, LangChain, ChromaDB, and local Ollama / Groq. 
It ingests a company knowledge base PDF and answers user questions strictly based on the extracted context, explicitly avoiding hallucination from pretrained knowledge and abstaining when evidence is insufficient.

## Architecture

- **Ingestion**: Extracted using `PyPDFLoader` and split into semantically coherent chunks with `RecursiveCharacterTextSplitter`.
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` executed locally via `langchain-huggingface` for zero-cost, high-speed consistency.
- **Vector Storage**: Persistent `ChromaDB` maintaining deterministic document and chunk IDs for idempotent upserts.
- **RAG Orchestration**: Strict query grounding and citation verification. Cross-validates LLM-cited chunk IDs against retrieved chunks and forces abstention if ungrounded.
- **Generation**: Flexible dual-provider support:
  - **Local Ollama (Default)**: Private, offline inference using `llama3` via `langchain-ollama`.
  - **Groq API**: High-speed cloud inference using `llama-3.3-70b-versatile` via `langchain-groq`.
- **API**: FastAPI web application with interactive Swagger documentation.

## Prerequisites

- Python 3.10+ (tested on Python 3.9/3.11)
- Either:
  - **Local Ollama**: Install from [ollama.com](https://ollama.com) and pull `llama3`:
    ```bash
    ollama run llama3
    ```
  - **OR Groq API Key**: A free key from [console.groq.com/keys](https://console.groq.com/keys)

## Setup

1. **Virtual Environment & Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and configure your chosen provider:
   ```bash
   cp .env.example .env
   ```
   - For **Local Ollama** (default):
     ```env
     LLM_PROVIDER=ollama
     OLLAMA_BASE_URL=http://localhost:11434
     OLLAMA_MODEL=llama3
     ```
   - For **Groq API**:
     ```env
     LLM_PROVIDER=groq
     GROQ_API_KEY=your_groq_api_key_here
     GROQ_MODEL=llama-3.3-70b-versatile
     ```

3. **Knowledge Base PDF**:
   The company knowledge base PDF is located at:
   `data/source/knowledge_base.pdf`

## Usage

### 1. Ingestion

To parse, chunk, and index the PDF into ChromaDB:
```bash
python -m scripts.ingest
```
Use `--rebuild` to wipe the existing vector collection and reindex from scratch:
```bash
python -m scripts.ingest --rebuild
```

### 2. Starting the API

Run the FastAPI server with hot-reload:
```bash
uvicorn app.main:app --reload
```
Access the interactive Swagger UI at: **http://127.0.0.1:8000/docs**

### API Endpoints

**Chat**  
`POST /chat`
```json
{
  "question": "Who is the founder of Agarwal Constructions?"
}
```
*Response:*
```json
{
  "answer": "Rajesh Agarwal",
  "status": "answered",
  "sources": [
    {
      "source": "knowledge_base.pdf",
      "page": 7,
      "chunk_id": "doc_cd10c5fe_p7_c6",
      "excerpt": "..."
    }
  ],
  "retrieval": {
    "chunks_retrieved": 5,
    "chunks_used": 1
  }
}
```

**Health**  
`GET /health`  
*Returns process liveness (`{"status": "ok", "service": "company-knowledge-rag"}`).*

**Readiness**  
`GET /ready`  
*Confirms whether the ChromaDB vector store is populated and ready for queries.*

## Testing and Evaluation

### Automated Unit Tests
Run the test suite (100% mocked, runs in <2 seconds without external API calls):
```bash
pytest
```
*Result: 27 passed.*

### Real-Document Evaluation Benchmark
Run the end-to-end evaluation benchmark over the 17-question dataset (`evaluation/questions.json`):
```bash
python -m evaluation.run_evaluation
```
**Evaluation Benchmark Results (with local Ollama `llama3`):**
- **Answerable Queries Answered:** 12 / 12 (**100.0%**) with verified citations.
- **Abstention Accuracy on Out-of-Scope Questions:** 5 / 5 (**100.0%**).
- **Retrieval Recall@5:** 50.00%.

## Security Notes
- `.env` is listed in `.gitignore` and never committed to GitHub.
- Proprietary vector DB files (`chroma_db/`) remain local and untracked.

## Demo Plan (3–5 Minutes Loom Video)
1. **Introduction & Structure**: Walk through the directory layout (`app/`, `data/`, `scripts/`, `evaluation/`).
2. **Ingestion Demo**: Run `python -m scripts.ingest --rebuild` to show clean extraction, chunking, and ChromaDB indexing.
3. **Start API**: Run `uvicorn app.main:app --reload` and open `http://127.0.0.1:8000/docs`.
4. **Answerable Query Demo**: 
   - Ask *"Who is the founder of Agarwal Constructions?"* -> Show answer `"Rajesh Agarwal"`, page 7 citation, and chunk ID.
   - Ask *"What is the head office address?"* -> Show `"Central Tower, 277 BB Ganguly Street, Kolkata – 700012"`.
5. **Abstention Query Demo**: 
   - Ask *"What is the company's 30-day refund policy?"* or *"What was the revenue in 2023?"*
   - Show that the response abstains cleanly with `status: "insufficient_evidence"` and empty sources.
6. **Testing & Evaluation**:
   - Run `pytest` to demonstrate 27 passed unit tests.
   - Run `python -m evaluation.run_evaluation` to show the 100% answer accuracy and 100% abstention rate.

## License
MIT License
