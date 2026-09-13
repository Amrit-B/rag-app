import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

ENV_PATH = Path(__file__).parents[2] / ".env"
load_dotenv(ENV_PATH)


def _build_llm(model_name: str, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
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
# rate limits (RPM and RPD) per model quota pool. Each model can be overridden via .env.

def get_router_llm() -> ChatGoogleGenerativeAI:
    """Lightweight & fast routing: default gemini-3.5-flash-lite."""
    model = os.getenv("ROUTER_MODEL", "gemini-3.5-flash-lite")
    return _build_llm(model, temperature=0.0)


def get_retrieval_grader_llm() -> ChatGoogleGenerativeAI:
    """Frequent per-chunk document relevance grading: default gemini-3.5-flash-lite."""
    model = os.getenv("RETRIEVAL_GRADER_MODEL", "gemini-3.5-flash-lite")
    return _build_llm(model, temperature=0.0)


def get_generator_llm() -> ChatGoogleGenerativeAI:
    """Core grounded response synthesis: default gemini-3.6-flash."""
    model = os.getenv("GENERATOR_MODEL", "gemini-3.6-flash")
    return _build_llm(model, temperature=0.0)


def get_hallucination_llm() -> ChatGoogleGenerativeAI:
    """High-reasoning groundedness & fact verification: default gemini-3.7-flash."""
    model = os.getenv("HALLUCINATION_MODEL", "gemini-3.7-flash")
    return _build_llm(model, temperature=0.0)


def get_answer_grader_llm() -> ChatGoogleGenerativeAI:
    """Final answer quality evaluation: default gemini-flash-latest."""
    model = os.getenv("ANSWER_GRADER_MODEL", "gemini-flash-latest")
    return _build_llm(model, temperature=0.0)


def get_evaluator_llm() -> ChatGoogleGenerativeAI:
    """Automated Ragas benchmark evaluation: default gemini-3.7-flash."""
    model = os.getenv("EVALUATOR_MODEL", "gemini-3.7-flash")
    return _build_llm(model, temperature=0.0)
