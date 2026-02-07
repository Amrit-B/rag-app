from pydantic import BaseModel, Field
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from dotenv import load_dotenv

load_dotenv()
embedding_model = get_registry().get("sentence-transformers").create(name="all-MiniLM-L6-v2", device="cpu")

EMBEDDING_DIM = 384

class ChunkArticle(LanceModel):
    doc_id: str
    chunk_id: str
    filepath: str
    filename: str
    owner_id: str = Field(description="ID of the user who uploaded the document")
    content: str = embedding_model.SourceField()
    embedding: Vector(EMBEDDING_DIM) = embedding_model.VectorField()

class Prompt(BaseModel):
    prompt: str = Field(description= 'prompt from user, if empty consider it as missing')