from typing import List, Optional, Any
from typing_extensions import TypedDict
from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    Represents the state of our agentic RAG graph.

    Attributes:
        question: Original or rewritten question
        generation: LLM generated answer
        web_search: Flag indicating whether to invoke web search
        documents: List of retrieved / filtered Document objects
        user_id: ID of the authenticated user to isolate documents
        chat_history: Prior conversation turns
        loop_step: Counter to prevent infinite hallucination / correction loops
        sources: Structured citation metadata (filename, snippet, url)
        route_taken: Tracks which path was chosen ('vectorstore' or 'websearch')
    """
    question: str
    generation: Optional[str]
    web_search: bool
    documents: List[Document]
    user_id: Optional[str]
    chat_history: Optional[List[dict]]
    loop_step: int
    sources: Optional[List[dict]]
    route_taken: Optional[str]
