from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.graph.llm import get_retrieval_grader_llm


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
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


retrieval_grader = get_retrieval_grader()
