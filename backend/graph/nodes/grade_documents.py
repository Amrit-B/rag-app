from typing import Any, Dict
from backend.graph.chains.retrieval_grader import retrieval_grader
from backend.graph.state import GraphState


def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question.
    If any document is not relevant, or if no documents were found,
    sets a flag to run web search.

    Args:
        state: Current graph state

    Returns:
        Filtered relevant documents and updated web_search flag.
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state.get("documents") or []

    filtered_docs = []
    web_search = False

    if not documents:
        print("---NO DOCUMENTS FOUND: TRIGGERING WEB SEARCH---")
        return {"documents": [], "question": question, "web_search": True}

    for d in documents:
        try:
            score = retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
            )
            # pyrefly: ignore [missing-attribute]
            grade = score.binary_score
            if grade.strip().lower() == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                web_search = True
        except Exception as e:
            print(f"Error grading document: {e}. Defaulting to keeping document.")
            filtered_docs.append(d)

    # If all docs were filtered out, trigger web search
    if not filtered_docs:
        web_search = True

    return {
        "documents": filtered_docs,
        "question": question,
        "web_search": web_search,
    }
