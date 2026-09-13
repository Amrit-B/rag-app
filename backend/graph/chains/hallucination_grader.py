from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.graph.llm import get_hallucination_llm


class GradeHallucinations(BaseModel):
    """Binary score for whether LLM generation is grounded in facts."""
    binary_score: bool = Field(
        description="Answer is grounded in the facts, True or False"
    )


def get_hallucination_grader():
    llm = get_hallucination_llm()
    structured_llm_grader = llm.with_structured_output(GradeHallucinations)

    system = (
        "You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.\n"
        "Return True if the answer is grounded in and directly supported by the set of facts.\n"
        "Return False if the answer includes unsupported assertions, fabricated claims, or hallucinations not present in the facts."
    )
    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Set of facts:\n\n{documents}\n\nLLM generation:\n\n{generation}"),
        ]
    )
    return hallucination_prompt | structured_llm_grader


hallucination_grader = get_hallucination_grader()
