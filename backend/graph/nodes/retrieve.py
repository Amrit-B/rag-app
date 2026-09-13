from typing import Any, Dict
from langchain_core.documents import Document
from backend.graph.state import GraphState
from backend.document_service import get_vector_db_table

RETRIEVAL_LIMIT = 5


def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieves documents from the LanceDB vector store filtered by user_id.

    Args:
        state: The current graph state

    Returns:
        Updated state dictionary with retrieved documents.
    """
    print("---RETRIEVE---")
    question = state["question"]
    user_id = state.get("user_id") or "default"

    documents: list[Document] = []
    try:
        table = get_vector_db_table()
        # Search LanceDB with user filtering
        query_results = (
            table.search(query=question)
            .where(f"owner_id = '{user_id}'")
            .limit(RETRIEVAL_LIMIT)
            .to_list()
        )

        for r in query_results:
            content = r.get("content") or ""
            metadata = {
                "doc_id": r.get("doc_id", ""),
                "chunk_id": r.get("chunk_id", ""),
                "filename": r.get("filename", "Unknown Document"),
                "filepath": r.get("filepath", ""),
                "source_type": "document",
                "score": r.get("_distance", 0.0),
            }
            documents.append(Document(page_content=content, metadata=metadata))

    except Exception as e:
        print(f"Retrieval warning: {e}")

    return {
        "documents": documents,
        "question": question,
        "route_taken": "vectorstore",
    }
