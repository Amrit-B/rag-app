from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.graph.llm import get_answer_grader_llm


class GradeAnswer(BaseModel):
    """Binary score for whether answer resolves the question."""
    binary_score: bool = Field(
        description="Answer addresses and resolves the question, True or False"
    )


def get_answer_grader():
    llm = get_answer_grader_llm()
    structured_llm_grader = llm.with_structured_output(GradeAnswer)

    system = (
        "You are a grader assessing whether an answer addresses / resolves a user question.\n"
        "Return True if the answer addresses the question directly and helpfully.\n"
        "Return False if the answer does not address the question, is evasive, or misses the core intent."
    )
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "User question:\n\n{question}\n\nLLM generation:\n\n{generation}"),
        ]
    )
    return answer_prompt | structured_llm_grader


answer_grader = get_answer_grader()
