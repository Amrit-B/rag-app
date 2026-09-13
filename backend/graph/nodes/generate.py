from typing import Any, Dict
from backend.graph.chains.generation import generation_chain
from backend.graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    """
    Generates answer using RAG generation chain and builds structured citation sources.

    Args:
        state: Current graph state

    Returns:
        Updated state with generation and sources metadata.
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state.get("documents") or []
    loop_step = state.get("loop_step", 0) + 1

    # Format context blocks
    context_blocks = []
    sources = []
    seen_sources = set()

    for d in documents:
        context_blocks.append(d.page_content)
        src_name = d.metadata.get("filename", "Document")
        src_url = d.metadata.get("url")
        src_type = d.metadata.get("source_type", "document")
        dedupe_key = (src_name, src_url)

        if dedupe_key not in seen_sources:
            seen_sources.add(dedupe_key)
            sources.append({
                "source": src_name,
                "snippet": d.page_content[:250].strip() + ("..." if len(d.page_content) > 250 else ""),
                "source_type": src_type,
                "url": src_url,
            })

    context_str = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant context available."

    try:
        generation = generation_chain.invoke({"context": context_str, "question": question})
    except Exception as e:
        generation = f"An error occurred during generation: {e}"

    return {
        "documents": documents,
        "question": question,
        "generation": generation,
        "sources": sources,
        "loop_step": loop_step,
    }
