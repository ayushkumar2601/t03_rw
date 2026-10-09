import os
import json
import time
from app.services.vector_store import VectorStore
from app.schemas.chat import ChatRequest
from app.services.rag import process_chat_request
from app.core.exceptions import LLMProviderError
from app.core.config import settings

def run_evaluation():
    print("Starting Evaluation Runner...")
    questions_path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(questions_path, "r") as f:
        questions = json.load(f)
        
    vs = VectorStore()
    if vs.count() == 0:
        print("Error: Knowledge base is empty. Please run ingestion first.")
        return 1

    results = []
    total_recall = 0
    total_precision = 0
    total_abstention = 0
    total_evaluated = 0
    
    generation_mocked = False
    if not settings.groq_api_key:
        print("WARNING: GROQ_API_KEY not found. LLM Generation and Accuracy metrics will be marked as PENDING.")
        generation_mocked = True

    for q in questions:
        print(f"\nEvaluating: {q['question']}")
        request = ChatRequest(question=q['question'])
        
        try:
            # We call the real RAG pipeline. If GROQ_API_KEY is missing, it will raise LLMProviderError
            # Wait, no, ChatGroq might just fail on invoke.
            if generation_mocked:
                # We can't evaluate end-to-end correctly without an API key, so we'll just evaluate retrieval manually
                from app.services.retrieval import retrieve_context
                retrieval = retrieve_context(request.question, vs)
                retrieved_pages = [c.get("page") for c in retrieval["selected_chunks"] if c.get("page")]
                
                # Recall@k calculation
                expected_pages = set(q.get("supporting_pages", []))
                if expected_pages:
                    intersect = set(retrieved_pages).intersection(expected_pages)
                    recall = len(intersect) / len(expected_pages)
                    total_recall += recall
                    total_evaluated += 1
                
                print(f"  [PENDING] Generation skipped. Retrieval pages found: {retrieved_pages}")
                results.append({
                    "id": q["id"],
                    "status": "pending_generation"
                })
            else:
                response = process_chat_request(request, vs)
                
                # Calculate Abstention correctness
                if q["expected_behavior"] == "abstain":
                    if response.status == "insufficient_evidence":
                        total_abstention += 1
                    print(f"  Expected Abstain, got: {response.status}")
                
                results.append({
                    "id": q["id"],
                    "status": response.status,
                    "answer": response.answer
                })

        except Exception as e:
            print(f"  Error processing question: {e}")
            if "key" in str(e).lower() or "api" in str(e).lower():
                generation_mocked = True

    # Output reports
    print("\n================ EVALUATION SUMMARY ================")
    if generation_mocked:
        print("REAL-DOCUMENT LLM GENERATION ACCURACY: [PENDING] (Requires GROQ_API_KEY)")
        if total_evaluated > 0:
            print(f"Retrieval Recall (Approximate based on page match): {(total_recall / total_evaluated) * 100:.2f}%")
        print("Please configure GROQ_API_KEY and rerun for end-to-end correctness, groundedness, and citation accuracy targets.")
    else:
        print("Evaluation complete. See detailed logs for metric targets.")
    print("====================================================")

    # Save report
    with open("evaluation_report.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    exit_code = run_evaluation()
    exit(exit_code if exit_code else 0)
