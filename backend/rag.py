from pydantic_ai import Agent
from backend.data_models import RagResponse
from backend.constants import VECTOR_DATABASE_PATH
import lancedb

rag_agent = Agent(
    model='google-gla:gemini-2.5-flash-lite',
    retries=1,
    system_prompt = (
    "You are an expert analyst answering strictly from retrieved documents.",
    "Use only the provided retrieved text. If none, say you cannot find the answer in the documents.",
    "Be concise (max 6 sentences). Return plain text, no JSON, no markdown, no code fences."
    ),
    output_type=RagResponse,
)

@rag_agent.tool_plain
def retreive_top_documents(query:str,k=3)->str:
    '''
    Uses vector search to find the closest k matching documents to the query
    '''
    vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
    results = vector_db['articles'].search(query=query).limit(k).to_list()
    if not results:
        return "No documents found for this query."
    top_result = results[0]
    content_snippet = top_result['content'][:800]
    return f"""
Filename: {top_result['filename']}
Filepath: {top_result['filepath']}
Content: {content_snippet}
"""