from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.graph.llm import get_router_llm


class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal["vectorstore", "websearch"] = Field(
        ...,
        description="Given a user question, choose whether to route it to internal vectorstore or external websearch.",
    )


def get_question_router():
    llm = get_router_llm()
    structured_llm_router = llm.with_structured_output(RouteQuery)

    system = (
        "You are an expert at routing a user question to a vectorstore or web search.\n"
        "The vectorstore contains documents, technical manuals, uploaded files, and stored knowledge base articles.\n"
        "Use 'vectorstore' for questions that likely relate to the user's uploaded documents, domain-specific concepts, or internal knowledge.\n"
        "For general broad knowledge, current world events, external news, or when the user explicitly asks to search the web, route to 'websearch'."
    )
    route_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{question}"),
        ]
    )
    return route_prompt | structured_llm_router


question_router = get_question_router()
