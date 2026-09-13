import os
from typing import Any, Dict
from langchain_core.documents import Document
from backend.graph.state import GraphState


def web_search(state: GraphState) -> Dict[str, Any]:
    """
    Executes a web search via the Tavily API to augment retrieved documents.
    If TAVILY_API_KEY is missing, gracefully adds an informative note.

    Args:
        state: Current graph state

    Returns:
        Updated documents list containing web search findings.
    """
    print("---WEB SEARCH (TAVILY)---")
    question = state["question"]
    documents = list(state.get("documents") or [])

    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not tavily_api_key:
        print("---NOTICE: TAVILY_API_KEY not configured. Skipping live web query---")
        web_notice = Document(
            page_content="[Notice: Tavily Web Search API key is not configured in .env. Answering based on available knowledge.]",
            metadata={
                "filename": "Web Search (Key Unset)",
                "source_type": "web",
                "url": "https://tavily.com",
            },
        )
        documents.append(web_notice)
        return {
            "documents": documents,
            "question": question,
            "web_search": False,
            "route_taken": "websearch" if not state.get("documents") else "hybrid",
        }

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=tavily_api_key)
        response = client.search(query=question, max_results=3, search_depth="basic")
        results = response.get("results", [])

        for item in results:
            content = item.get("content", "")
            title = item.get("title", "Web Result")
            url = item.get("url", "")
            if content:
                doc = Document(
                    page_content=content,
                    metadata={
                        "filename": title,
                        "source_type": "web",
                        "url": url,
                    },
                )
                documents.append(doc)

        print(f"---TAVILY SEARCH RETURNED {len(results)} RESULTS---")

    except Exception as e:
        print(f"---TAVILY SEARCH FAILED: {e}---")
        fallback_doc = Document(
            page_content=f"[Web search encountered an issue: {e}]",
            metadata={"filename": "Tavily Search Error", "source_type": "web"},
        )
        documents.append(fallback_doc)

    return {
        "documents": documents,
        "question": question,
        "web_search": False,
        "route_taken": "websearch" if not state.get("documents") else "hybrid",
    }
