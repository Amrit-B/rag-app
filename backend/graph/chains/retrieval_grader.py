from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.graph.llm import get_retrieval_grader_llm


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


class BatchGradeDocuments(BaseModel):
    """Batch relevance evaluation for retrieved document chunks."""
    relevant_indices: list[int] = Field(
        default_factory=list,
        description="0-indexed list of integers corresponding to document chunks that are relevant to the user question.",
    )


def get_retrieval_grader():
    llm = get_retrieval_grader_llm()
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    system = (
        "You are a grader assessing relevance of a retrieved document to a user question.\n"
        "If the document contains keywords, concepts, or semantic meaning related to the user question, grade it as relevant.\n"
        "It does not need to be a stringent test. The goal is to filter out completely erroneous or off-topic retrievals.\n"
        "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
    )
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document:\n\n{document}\n\nUser question: {question}"),
        ]
    )
    return grade_prompt | structured_llm_grader


def get_batch_retrieval_grader():
    llm = get_retrieval_grader_llm()
    structured_llm_grader = llm.with_structured_output(BatchGradeDocuments)

    system = (
        "You are an expert evaluator assessing the relevance of candidate document chunks to a user question.\n"
        "You will be given numbered document chunks: [Chunk 0], [Chunk 1], etc.\n"
        "For each chunk, determine if it contains keywords, concepts, or semantic meaning related to the user question.\n"
        "It does not need to be a stringent test; filter out only completely off-topic or irrelevant chunks.\n"
        "Return the 0-indexed list of indices (relevant_indices) for chunks that are relevant to answering the question."
    )
    batch_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "User question: {question}\n\nCandidate Document Chunks:\n{documents}"),
        ]
    )
    return batch_prompt | structured_llm_grader


retrieval_grader = get_retrieval_grader()
batch_retrieval_grader = get_batch_retrieval_grader()

