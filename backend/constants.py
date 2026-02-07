from pathlib import Path
import os
import sys

# Location for per-user auth DB (SQLite)
AUTH_DB_PATH = Path(__file__).parents[1] / "data" / "auth.db"

# JWT secret (override with env var in production)
SECRET_KEY = os.getenv('RAG_SECRET_KEY')
if not SECRET_KEY:
    sys.exit('Missing RAG_SECRET_KEY environment variable; set it before starting the app.')

DATA_PATH = Path(__file__).parents[1] / "data"
VECTOR_DATABASE_PATH = Path(__file__).parents[1] / "knowledge_base"
