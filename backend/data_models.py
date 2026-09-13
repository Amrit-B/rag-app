from typing import Optional, List, Any
from pydantic import BaseModel, Field
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

embedding_model = get_registry().get("sentence-transformers").create(name="all-MiniLM-L6-v2", device="cpu")
EMBEDDING_DIM = 384


class ChunkArticle(LanceModel):
    doc_id: str
    chunk_id: str
    filepath: str
    filename: str
    owner_id: str = Field(description="ID of the user who uploaded the document")
    content: str = embedding_model.SourceField()
    # pyrefly: ignore [invalid-annotation]
    embedding: Vector(EMBEDDING_DIM) = embedding_model.VectorField()


# Auth Models
class RegisterModel(BaseModel):
    username: str
    password: str


class LoginModel(BaseModel):
    username: str
    password: str


# Query & Chat Models
class Prompt(BaseModel):
    prompt: str = Field(description="User prompt or question")
    session_id: Optional[str] = Field(default=None, description="Optional chat session ID")


class CitationSource(BaseModel):
    source: str = Field(description="Source name, title, or filename")
    snippet: str = Field(description="Relevant excerpt or summary")
    source_type: str = Field(default="document", description="'document' or 'web'")
    url: Optional[str] = Field(default=None, description="URL if web source")


class RAGQueryResponse(BaseModel):
    answer: str
    filepath: str
    sources: List[CitationSource] = []
    route_taken: Optional[str] = "vectorstore"
    session_id: Optional[str] = None


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    sources: List[Any] = []
    route_taken: Optional[str] = None
    created_at: str


class DocumentMetadataResponse(BaseModel):
    doc_id: str
    filename: str
    filepath: str
    file_size_bytes: int
    chunk_count: int
    status: str
    created_at: Optional[str] = None


class UploadJobResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    error: Optional[str] = None
