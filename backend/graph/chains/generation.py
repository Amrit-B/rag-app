from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.graph.llm import get_generator_llm


def get_generation_chain():
    llm = get_generator_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert AI assistant for question-answering tasks.\n"
                "Use the following pieces of retrieved context to answer the user's question.\n"
                "Guidelines:\n"
                "1. Answer strictly based on the provided context.\n"
                "2. Copy proper nouns, numbers, dates, and technical terms accurately.\n"
                "3. If the context does not contain the answer, state clearly: 'I could not find sufficient information in the provided context.'\n"
                "4. Be structured, precise, and concise.\n\n"
                "Retrieved Context:\n{context}",
            ),
            ("human", "Question: {question}"),
        ]
    )
    return prompt | llm | StrOutputParser()


generation_chain = get_generation_chain()
