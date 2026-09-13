import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

ENV_PATH = Path(__file__).parents[2] / ".env"
# Force reload with override=True so fresh keys in .env take precedence
load_dotenv(ENV_PATH, override=True)


def _build_llm(model_name: str, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is missing. Set it in .env before running.")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
    )


def get_llm(model: str = "gemini-3.6-flash", temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Generic LLM factory."""
    return _build_llm(model, temperature)


# Free Tier Multi-Model Distribution:
# Distributing distinct graph roles across separate Gemini models to optimize
# rate limits (RPM and RPD) per model quota pool.

def get_router_llm() -> ChatGoogleGenerativeAI:
    """Lightweight & fast routing: uses gemini-3.5-flash-lite."""
    return _build_llm("gemini-3.5-flash-lite", temperature=0.0)


def get_retrieval_grader_llm() -> ChatGoogleGenerativeAI:
    """Frequent per-chunk document relevance grading: uses gemini-3.5-flash-lite."""
    return _build_llm("gemini-3.5-flash-lite", temperature=0.0)


def get_generator_llm() -> ChatGoogleGenerativeAI:
    """Core grounded response synthesis: uses gemini-3.6-flash."""
    return _build_llm("gemini-3.6-flash", temperature=0.0)


def get_hallucination_llm() -> ChatGoogleGenerativeAI:
    """High-reasoning groundedness & fact verification: uses gemini-3.7-flash."""
    return _build_llm("gemini-3.7-flash", temperature=0.0)


def get_answer_grader_llm() -> ChatGoogleGenerativeAI:
    """Final answer quality evaluation: uses gemini-flash-latest."""
    return _build_llm("gemini-flash-latest", temperature=0.0)


def get_evaluator_llm() -> ChatGoogleGenerativeAI:
    """Automated Ragas benchmark evaluation: uses gemini-3.7-flash."""
    return _build_llm("gemini-3.7-flash", temperature=0.0)
