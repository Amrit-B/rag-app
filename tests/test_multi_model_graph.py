import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.graph.llm import (
    get_router_llm,
    get_retrieval_grader_llm,
    get_generator_llm,
    get_hallucination_llm,
    get_answer_grader_llm,
    get_evaluator_llm,
)
from backend.graph.chains.router import question_router
from backend.graph.chains.retrieval_grader import retrieval_grader
from backend.graph.chains.generation import generation_chain
from backend.graph.chains.hallucination_grader import hallucination_grader
from backend.graph.chains.answer_grader import answer_grader


def test_model_assignments():
    print("Verifying model assignments for multi-model distribution...", flush=True)
    router = get_router_llm()
    retrieval_grader_llm = get_retrieval_grader_llm()
    generator = get_generator_llm()
    hallucination = get_hallucination_llm()
    answer_grader_llm = get_answer_grader_llm()
    evaluator = get_evaluator_llm()

    print(f"Router Model:             {router.model}", flush=True)
    print(f"Retrieval Grader Model:   {retrieval_grader_llm.model}", flush=True)
    print(f"Generator Model:          {generator.model}", flush=True)
    print(f"Hallucination Grader:     {hallucination.model}", flush=True)
    print(f"Answer Grader Model:      {answer_grader_llm.model}", flush=True)
    print(f"Evaluator Model:          {evaluator.model}", flush=True)

    assert router.model == "gemini-3.5-flash-lite"
    assert retrieval_grader_llm.model == "gemini-3.5-flash-lite"
    assert generator.model == "gemini-3.6-flash"
    assert hallucination.model == "gemini-3.7-flash"
    assert answer_grader_llm.model == "gemini-flash-latest"
    assert evaluator.model == "gemini-3.7-flash"
    print("[PASS] All distinct model assignments verified!", flush=True)


def test_individual_chains():
    print("\n--- TESTING INDIVIDUAL MULTI-MODEL CHAINS ---", flush=True)
    print("1. Testing Router chain (gemini-3.5-flash-lite)...", flush=True)
    route_res = question_router.invoke({"question": "What is Python?"})
    print(f"   Router output: {route_res}", flush=True)

    print("\n2. Testing Generation chain (gemini-3.6-flash)...", flush=True)
    gen_res = generation_chain.invoke({"context": "Python was created by Guido van Rossum.", "question": "Who created Python?"})
    print(f"   Generation output: {gen_res}", flush=True)

    print("\n3. Testing Hallucination Grader chain (gemini-3.7-flash)...", flush=True)
    hal_res = hallucination_grader.invoke({"documents": "Python was created by Guido van Rossum.", "generation": gen_res})
    print(f"   Hallucination grader output: {hal_res}", flush=True)

    print("\n4. Testing Answer Grader chain (gemini-flash-latest)...", flush=True)
    ans_res = answer_grader.invoke({"question": "Who created Python?", "generation": gen_res})
    print(f"   Answer grader output: {ans_res}", flush=True)

    print("\n5. Testing Retrieval Grader chain (gemini-3.5-flash-lite)...", flush=True)
    ret_res = retrieval_grader.invoke({"document": "Python was created by Guido van Rossum.", "question": "Who created Python?"})
    print(f"   Retrieval grader output: {ret_res}", flush=True)

    print("\n[PASS] All individual specialized chains executed successfully!", flush=True)


if __name__ == "__main__":
    test_model_assignments()
    test_individual_chains()
    print("\nALL MULTI-MODEL DISTRIBUTION TESTS PASSED!")
