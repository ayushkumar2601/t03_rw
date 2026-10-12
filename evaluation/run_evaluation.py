import json
import os
from typing import Any, Dict, List

import httpx

from app.core.config import settings
from app.schemas.chat import ChatRequest
from app.services.rag import process_chat_request
from app.services.retrieval import retrieve_context
from app.services.vector_store import VectorStore


def check_provider_availability() -> bool:
    """Check if the configured LLM provider is available."""
    provider = (settings.llm_provider or "ollama").strip().lower()
    if provider == "ollama":
        try:
            r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False
    elif provider == "groq":
        return bool(settings.groq_api_key)
    return False


def run_evaluation():
    print(f"Starting Evaluation Runner (Provider: {settings.llm_provider})...")
    questions_path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(questions_path, "r") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    vs = VectorStore()
    if vs.count() == 0:
        print("Error: Knowledge base is empty. Please run ingestion first.")
        return 1

    provider_ready = check_provider_availability()
    if not provider_ready:
        print(
            f"WARNING: LLM Provider '{settings.llm_provider}' is not ready/configured. "
            "LLM Generation and Accuracy metrics will be marked as PENDING."
        )

    results = []
    total_recall = 0.0
    recall_count = 0
    total_abstain_expected = 0
    correct_abstentions = 0
    total_answer_expected = 0
    correct_answers = 0

    for q in questions:
        print(f"\nEvaluating: {q['question']}")
        request = ChatRequest(question=q["question"])

        # 1. Retrieval assessment
        retrieval = retrieve_context(request.question, vs)
        retrieved_pages = [
            c.get("page") for c in retrieval["selected_chunks"] if c.get("page")
        ]
        expected_pages = set(q.get("supporting_pages", []))
        if expected_pages:
            intersect = set(retrieved_pages).intersection(expected_pages)
            recall = len(intersect) / len(expected_pages)
            total_recall += recall
            recall_count += 1
            print(f"  Retrieval pages: {retrieved_pages} (Recall: {recall:.2f})")
        else:
            print(f"  Retrieval pages: {retrieved_pages}")

        # 2. End-to-end Generation assessment
        if not provider_ready:
            results.append({"id": q["id"], "status": "pending_generation"})
            continue

        try:
            response = process_chat_request(request, vs)
            expected_behavior = q.get("expected_behavior", "answer")

            if expected_behavior == "abstain":
                total_abstain_expected += 1
                if response.status == "insufficient_evidence":
                    correct_abstentions += 1
                    print("  [PASS] Successfully abstained on unsupported question.")
                else:
                    print(f"  [FAIL] Expected abstention, got status: {response.status}")
            else:
                total_answer_expected += 1
                if response.status == "answered":
                    correct_answers += 1
                    print(f"  [PASS] Answered with {len(response.sources)} citations.")
                else:
                    print(f"  [INFO] Model abstained: {response.answer[:80]}...")

            results.append(
                {
                    "id": q["id"],
                    "status": response.status,
                    "answer": response.answer,
                    "sources_count": len(response.sources),
                }
            )
        except Exception as e:
            print(f"  Error processing question: {e}")
            results.append({"id": q["id"], "status": "error", "error": str(e)})

    # Output reports
    print("\n================ EVALUATION SUMMARY ================")
    print(f"LLM Provider: {settings.llm_provider}")
    if recall_count > 0:
        avg_recall = (total_recall / recall_count) * 100
        print(f"Retrieval Recall@k: {avg_recall:.2f}% ({recall_count} questions evaluated)")

    if provider_ready:
        if total_answer_expected > 0:
            print(
                f"Answerable Queries Answered: {correct_answers}/{total_answer_expected} "
                f"({(correct_answers / total_answer_expected) * 100:.1f}%)"
            )
        if total_abstain_expected > 0:
            print(
                f"Abstention Accuracy: {correct_abstentions}/{total_abstain_expected} "
                f"({(correct_abstentions / total_abstain_expected) * 100:.1f}%)"
            )
    else:
        print("REAL-DOCUMENT LLM GENERATION: [PENDING] (Provider not accessible)")
    print("====================================================")

    # Save report
    report_path = "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved evaluation report to {report_path}")
    return 0


if __name__ == "__main__":
    exit_code = run_evaluation()
    exit(exit_code if exit_code else 0)
