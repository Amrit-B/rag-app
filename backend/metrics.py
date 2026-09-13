from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

# Prometheus Metrics
RAG_QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total RAG queries processed",
    ["route_taken"],
)

RAG_RETRIEVAL_DURATION_SECONDS = Histogram(
    "rag_retrieval_duration_seconds",
    "Time spent executing vector search retrieval in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

RAG_INGESTION_TOTAL = Counter(
    "rag_documents_ingested_total",
    "Total documents ingested into vector store",
    ["status"],
)

RAG_INGESTION_DURATION_SECONDS = Histogram(
    "rag_ingestion_duration_seconds",
    "Time spent ingesting and chunking a document in seconds",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

RAG_GRADER_DECISIONS_TOTAL = Counter(
    "rag_grader_decisions_total",
    "Relevance decisions made by document grader",
    ["verdict"],
)

RAG_HALLUCINATION_DECISIONS_TOTAL = Counter(
    "rag_hallucination_decisions_total",
    "Groundedness decisions made by hallucination grader",
    ["verdict"],
)

RAG_WEB_SEARCHES_TOTAL = Counter(
    "rag_web_searches_total",
    "Tavily web searches triggered",
    ["status"],
)


def setup_metrics(app: FastAPI) -> None:
    """Instruments FastAPI application to expose Prometheus metrics on /metrics."""
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/metrics", "/docs", "/openapi.json"],
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
