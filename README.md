# RAG Application

A retrieval-augmented generation (RAG) system combining document search with AI-powered responses.

## Features

- Document Upload and Indexing: Upload PDF documents which are automatically chunked and embedded
- Semantic Search: Query documents using embeddings for contextual relevance
- AI-Powered Responses: Generate answers using Google Gemini API with retrieved context
- User Authentication: Secure login and registration with JWT tokens
- Vector Database: LanceDB for efficient semantic search over document embeddings

## Tech Stack

- Backend: FastAPI with async processing
- Frontend: Streamlit
- Vector Database: LanceDB with sentence-transformers embeddings
- Database: SQLite for user authentication and metadata
- Authentication: JWT tokens with PBKDF2-SHA256 password hashing
- Containerization: Docker/Podman with automatic CI/CD deployment
- Infrastructure: Oracle Cloud VM with GitHub Actions automation

## Quick Start

### Local Development

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1 - Backend
python -m uvicorn api:app --reload

# Terminal 2 - Frontend
streamlit run frontend/app.py
```

### Docker Deployment

```bash
docker-compose up -d
```

Access the application at http://localhost:8501

## Environment Variables

Create a `.env` file with:

```
GOOGLE_API_KEY=your_google_api_key
RAG_SECRET_KEY=your_secret_key
```

## API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /query` - Query documents with RAG
- `POST /documents` - Upload documents
- `GET /documents` - List user documents
- `DELETE /documents/{doc_id}` - Delete document
- `POST /reset` - Reset knowledge base

## Deployment

Automated CI/CD pipeline via GitHub Actions:
1. Push code to main branch
2. GitHub Actions builds Docker image
3. Image pushed to Docker Hub
4. SSH deployment to Oracle Cloud VM
5. Containers restart with latest image

## License

MIT
