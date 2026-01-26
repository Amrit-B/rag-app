from pydantic import BaseModel, Field
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from dotenv import load_dotenv

load_dotenv()
embedding_model = get_registry().get("sentence-transformers").create(name="all-MiniLM-L6-v2", device="cpu")

EMBEDDING_DIM = 384

class Article(LanceModel):
    doc_id: str
    filepath: str
    filename: str = Field(description = "The stem of the file without suffix")
    content: str = embedding_model.SourceField()
    embedding: Vector(EMBEDDING_DIM) = embedding_model.VectorField()

class Prompt(BaseModel):
    prompt: str = Field(description= 'prompt from user, if empty consider it as missing')

class RagResponse(BaseModel):
    filename: str = Field(description="filename of the retrived file without suffix")
    filepath: str = Field(description='absolute path to the retrived file')
    answer: str = Field(description='answer based in the retrived file')
    