import os
import json
import argparse
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

from backend.graph.llm import get_evaluator_llm
from backend.graph import app


DEFAULT_BENCHMARK_SAMPLES = [
    {
        "user_input": "What is the primary function of the LangGraph RAG pipeline?",
        "reference": "The LangGraph RAG pipeline orchestrates an agentic self-corrective retrieval-augmented generation workflow with query routing, document grading, web search fallback, and hallucination evaluation.",
    },
    {
        "user_input": "How does the system handle insufficient or missing document context?",
        "reference": "When retrieved documents fail the relevance grading check or are empty, the workflow triggers a Tavily web search fallback to gather external context.",
    },
    {
        "user_input": "What vector database is used and why?",
        "reference": "LanceDB is used as the embedded columnar vector store for local execution, low memory overhead, and disk-backed Arrow storage.",
    },
]


def run_evaluation(
    samples: list[dict] | None = None,
    output_path: str | Path | None = None,
    user_id: str = "default",
) -> dict:
    """
    Executes automated RAG evaluation using Ragas measuring:
    1. Context Precision (signal-to-noise ratio in retrieval)
    2. Faithfulness (groundedness vs retrieved facts)
    3. Answer Relevance (alignment with user question)
    """
    eval_samples = samples or DEFAULT_BENCHMARK_SAMPLES

    questions = []
    responses = []
    retrieved_contexts = []
    ground_truths = []

    print(f"\n--- RUNNING PIPELINE OVER {len(eval_samples)} TEST SAMPLES ---")

    for i, item in enumerate(eval_samples):
        q = item["user_input"]
        ref = item.get("reference", "")
        print(f"\n[{i+1}/{len(eval_samples)}] Evaluating Query: '{q}'")

        try:
            result = app.invoke({
                "question": q,
                "user_id": user_id,
                "documents": [],
                "web_search": False,
                "loop_step": 0,
            })
            answer = result.get("generation") or "No answer produced"
            docs = result.get("documents") or []
            contexts = [d.page_content for d in docs] if docs else ["No context retrieved."]
        except Exception as e:
            answer = f"Pipeline execution failed: {e}"
            contexts = ["Execution error occurred."]

        questions.append(q)
        responses.append(answer)
        retrieved_contexts.append(contexts)
        ground_truths.append(ref)

    dataset_dict = {
        "user_input": questions,
        "response": responses,
        "retrieved_contexts": retrieved_contexts,
        "reference": ground_truths,
    }

    eval_dataset = Dataset.from_dict(dataset_dict)

    print("\n--- COMPUTING RAGAS METRICS ---")
    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

        evaluator_llm = LangchainLLMWrapper(get_evaluator_llm())
        evaluator_embeddings = LangchainEmbeddingsWrapper(
            SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        )

        results = evaluate(
            eval_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
        )
        # pyrefly: ignore [no-matching-overload]
        report = dict(results)
    except Exception as e:
        print(f"Ragas evaluation warning: {e}")
        report = {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "error": str(e),
        }

    output = {
        "sample_count": len(eval_samples),
        "scores": report,
        "samples": [
            {
                "question": questions[i],
                "response": responses[i],
                "contexts_count": len(retrieved_contexts[i]),
                "reference": ground_truths[i],
            }
            for i in range(len(questions))
        ],
    }

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Evaluation report saved to {out_p}")

    print("\n================ RAGAS EVALUATION SUMMARY ================")
    for k, v in report.items():
        if isinstance(v, (float, int)):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print("=========================================================\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Ragas evaluation for Agentic RAG")
    parser.add_argument("--output", default="reports/ragas_evaluation.json", help="Path to save evaluation report")
    parser.add_argument("--user-id", default="default", help="User ID for document retrieval")
    args = parser.parse_args()

    run_evaluation(output_path=args.output, user_id=args.user_id)
