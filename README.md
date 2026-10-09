# Company Knowledge Base RAG Chatbot

This project implements a Retrieval-Augmented Generation (RAG) Chatbot built with FastAPI, LangChain, ChromaDB, and Groq. 
It ingests a company knowledge base PDF and answers user questions strictly based on the extracted context, explicitly avoiding hallucination from pretrained knowledge.

## Architecture

- **Ingestion**: Extracted using `PyPDFLoader` and split into meaningful chunks with `RecursiveCharacterTextSplitter`.
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` executed locally for performance, consistency, and cost-efficiency.
- **Vector Storage**: Persistent `ChromaDB`. Maintains deterministic document and chunk IDs to allow idempotent upserts.
- **RAG Orchestration**: Built-in query grounding and rigorous citation validation. Validates LLM citations against available context and forces abstention if ungrounded.
- **Generation**: Powered by Groq LLM API (`llama-3.3-70b-versatile`) with structured Pydantic outputs ensuring well-formed JSON responses.
- **API**: FastAPI web application.

## Prerequisites

- Python 3.11
- A [Groq API Key](https://console.groq.com/keys)

## Setup

1. **Virtual Environment & Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and fill in your variables:
   ```bash
   cp .env.example .env
   ```
   **IMPORTANT**: You must add your `GROQ_API_KEY` to the `.env` file for Phase 2 API queries to succeed.

3. **PDF Placement**:
   Place your company knowledge base PDF at:
   `data/source/knowledge_base.pdf`

## Usage

### 1. Ingestion

To parse, chunk, and index the PDF:
```bash
python -m scripts.ingest
```
Use `--rebuild` if you want to explicitly wipe the database and start fresh.

### 2. Starting the API

Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```
Access the Swagger UI Documentation at: http://127.0.0.1:8000/docs

### API Endpoints

**Chat**
`POST /chat`
```json
{
  "question": "What is the company's refund policy?"
}
```
*Returns either a grounded answer with valid `sources` or an `insufficient_evidence` abstention if the PDF does not contain the answer.*

**Health**
`GET /health`
*Returns process liveness.*

**Readiness**
`GET /ready`
*Confirms if the ChromaDB vector store is populated and ready for queries.*

## Testing and Evaluation

Run the comprehensive unit test suite (does not require a real Groq Key):
```bash
pytest
```

To run the RAG end-to-end evaluation script over the provided dataset:
```bash
python -m evaluation.run_evaluation
```
**Evaluation Methodology:** 
The evaluation relies on a verified dataset (`evaluation/questions.json`) built directly from the `Agarwal Constructions` PDF. It tests Answerable (fact-retrieval), Unanswerable (abstention enforcement), Paraphrased, and Multi-passage inference questions. The pipeline strictly evaluates Retrieval Recall@k, Citation Accuracy, and the Groundedness of the LLM output. 
*Note: Due to API key boundaries, full LLM generation accuracy tests are marked as PENDING until you insert your `GROQ_API_KEY`.*

## Known Limitations
- OCR for scanned PDFs is not supported.
- LLM generation relies on Groq; network timeouts or rate limits will return HTTP 502.
- Vector search relevance uses standard L2 distance. A strict similarity threshold is configured via `RETRIEVAL_MIN_RELEVANCE`, but defaults to `0.0` (off) until empirically calibrated for the specific document.

## Troubleshooting
- **Missing Knowledge Base (HTTP 503)**: Ensure you've run the ingestion script. The `ChromaDB` directory must be fully populated.
- **Upstream Provider Error (HTTP 502)**: Verify your `GROQ_API_KEY` is correct, well-funded, and you are not exceeding rate limits.
- **Empty Responses**: Check if `RETRIEVAL_MIN_RELEVANCE` is set too strictly (low).

## Security Notes
- **Never commit `.env`!** Ensure it remains ignored by `.gitignore`. 
- Ensure that the generated DB caches (`chroma_db`) remain untracked to prevent leaking proprietary document snippets.

## Demo Plan (3-5 Minutes)
1. Show the `data/source/knowledge_base.pdf` location.
2. Run `python -m scripts.ingest --rebuild` to show fresh ingestion speed and logging.
3. Start the server with `uvicorn app.main:app --reload`.
4. Open the Swagger UI at `http://localhost:8000/docs`.
5. Submit an answerable question: *"What is the head office address?"* -> Show the grounded JSON citation and chunk mapping.
6. Submit an unanswerable question: *"What was the revenue in 2023?"* -> Show the graceful `insufficient_evidence` fallback and empty citation array.
7. Run the test suite `pytest` to demonstrate 100% pass rates across 27+ tests.

## License
MIT License
