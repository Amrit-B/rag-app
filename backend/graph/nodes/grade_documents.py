import re
from typing import Any, Dict
from backend.graph.chains.retrieval_grader import batch_retrieval_grader, retrieval_grader
from backend.graph.state import GraphState


def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether retrieved documents are relevant to the question in a single batch call.
    Avoids 4-5 sequential round-trips and respects user instructions (e.g. 'no web search').

    Args:
        state: Current graph state

    Returns:
        Filtered relevant documents and updated web_search flag.
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION (BATCH)---")
    question = state["question"]
    documents = state.get("documents") or []

    # Check if user explicitly asked not to search the web
    user_requested_no_web = bool(
        re.search(
            r"\b(dont|don't|do not|no)\s+(search\s+the\s+web|search\s+web|web\s*search)\b",
            question,
            re.IGNORECASE,
        )
    )

    filtered_docs = []
    web_search = False

    if not documents:
        print("---NO DOCUMENTS FOUND---")
        if user_requested_no_web:
            print("---USER REQUESTED NO WEB SEARCH: SKIPPING WEB SEARCH---")
            return {"documents": [], "question": question, "web_search": False}
        return {"documents": [], "question": question, "web_search": True}

    # Format chunks with chunk index for single batch prompt
    formatted_chunks = []
    for idx, doc in enumerate(documents):
        snippet = doc.page_content[:600].strip()
        formatted_chunks.append(f"[Chunk {idx}]:\n{snippet}")
    docs_block = "\n\n".join(formatted_chunks)

    try:
        batch_result = batch_retrieval_grader.invoke(
            {"question": question, "documents": docs_block}
        )
        # pyrefly: ignore [missing-attribute]
        relevant_indices = set(getattr(batch_result, "relevant_indices", []))
        for idx, doc in enumerate(documents):
            if idx in relevant_indices:
                filtered_docs.append(doc)
        print(f"---BATCH GRADE: Kept {len(filtered_docs)} of {len(documents)} chunks in 1 API call---")
    except Exception as e:
        print(f"Batch grading fallback due to: {e}. Keeping all retrieved documents.")
        filtered_docs = list(documents)

    # If no documents are relevant, check whether we can search the web
    if not filtered_docs:
        if user_requested_no_web:
            print("---NO RELEVANT DOCS, BUT USER REQUESTED NO WEB SEARCH---")
            web_search = False
        else:
            print("---NO RELEVANT DOCS FOUND: TRIGGERING WEB SEARCH---")
            web_search = True
    else:
        # If we have relevant documents from the user's files, do NOT force web search
        web_search = False

    return {
        "documents": filtered_docs,
        "question": question,
        "web_search": web_search,
    }

