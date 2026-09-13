from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Automatically load environment variables from project root .env, overriding terminal vars
load_dotenv(Path(__file__).parents[1] / ".env", override=True)

AUTH_DB_PATH = Path(__file__).parents[1] / "data" / "auth.db"

SECRET_KEY = os.getenv("RAG_SECRET_KEY")
if not SECRET_KEY:
    # Fallback to default secret for local dev if missing
    SECRET_KEY = "dev-fallback-rag-secret-key-change-in-production"

DATA_PATH = Path(__file__).parents[1] / "data"
VECTOR_DATABASE_PATH = Path(__file__).parents[1] / "knowledge_base"
