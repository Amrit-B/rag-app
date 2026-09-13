from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from backend.graph.chains.answer_grader import answer_grader
from backend.graph.chains.hallucination_grader import hallucination_grader
from backend.graph.chains.router import RouteQuery, question_router
from backend.graph.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEBSEARCH
from backend.graph.nodes import generate, grade_documents, retrieve, web_search
from backend.graph.state import GraphState

load_dotenv()

MAX_CORRECTION_LOOPS = 2


def decide_to_generate(state: GraphState) -> str:
    print("---ASSESS GRADED DOCUMENTS---")
    if state.get("web_search"):
        print("---DECISION: NOT ALL DOCUMENTS ARE RELEVANT, INCLUDE WEB SEARCH---")
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE---")
        return GENERATE


def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state.get("documents") or []
    generation = state.get("generation") or ""
    loop_step = state.get("loop_step", 1)

    # Safety guard: prevent infinite hallucination / correction loops
    if loop_step > MAX_CORRECTION_LOOPS:
        print(f"---DECISION: MAX CORRECTION LOOPS ({MAX_CORRECTION_LOOPS}) REACHED. FINISHING---")
        return "max_retries_exceeded"

    if not documents:
        print("---NO DOCUMENTS: FINISHING DIRECTLY WITHOUT HALLUCINATION CHECK---")
        return "useful"

    docs_text = "\n\n".join([d.page_content for d in documents])

    try:
        score = hallucination_grader.invoke(
            {"documents": docs_text, "generation": generation}
        )
        # pyrefly: ignore [missing-attribute]
        is_grounded = score.binary_score
    except Exception as e:
        print(f"Hallucination grader error: {e}. Assuming grounded.")
        is_grounded = True

    if is_grounded:
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        try:
            score = answer_grader.invoke(
                {"question": question, "generation": generation}
            )
            # pyrefly: ignore [missing-attribute]
            answers_question = score.binary_score
        except Exception as e:
            print(f"Answer grader error: {e}. Assuming useful.")
            answers_question = True

        if answers_question:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION -> FALLBACK TO WEB SEARCH---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS -> RE-TRYING GENERATION---")
        return "not supported"


def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]
    try:
        # pyrefly: ignore [bad-assignment]
        source: RouteQuery = question_router.invoke({"question": question})
        if source.datasource == "websearch":
            print("---ROUTE QUESTION TO WEB SEARCH---")
            return WEBSEARCH
        else:
            print("---ROUTE QUESTION TO RETRIEVAL---")
            return RETRIEVE
    except Exception as e:
        print(f"Router error: {e}. Defaulting to retrieve.")
        return RETRIEVE


# Assemble the LangGraph workflow
# pyrefly: ignore [bad-specialization]
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, web_search)

# Conditional Entry Point from START
workflow.add_conditional_edges(
    START,
    route_question,
    {
        WEBSEARCH: WEBSEARCH,
        RETRIEVE: RETRIEVE,
    },
)

# Graph Edges
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)

workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)

workflow.add_edge(WEBSEARCH, GENERATE)

workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "not supported": GENERATE,
        "useful": END,
        "not useful": WEBSEARCH,
        "max_retries_exceeded": END,
    },
)

app = workflow.compile()
