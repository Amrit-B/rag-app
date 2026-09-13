# Agentic RAG Platform with LangGraph, LanceDB & Next.js

An enterprise-grade, self-reflective Retrieval-Augmented Generation (RAG) platform featuring **LangGraph control flow**, **LanceDB vector storage**, **SQLite persistence**, **Tavily web search fallback**, **Ragas automated evaluation**, and **Prometheus/Grafana observability**.

Based on the agentic RAG and self-corrective pattern ([emarco177/langgraph-course](https://github.com/emarco177/langgraph-course/tree/project/agentic-rag)).

---

## Key Features

- **Self-Reflective Multi-Step RAG (LangGraph)**:
  - **Question Router Chain**: Intelligently routes queries to local vector store or web search.
  - **Relevance Grader**: Evaluates retrieved document chunks against the prompt; filters noise.
  - **Tavily Web Search Fallback**: Automatically invokes external web search when local context is insufficient.
  - **Hallucination Grader**: Self-corrects responses if ungrounded claims are detected.
  - **Answer Grader**: Verifies the synthesized response directly addresses the question.
- **Modern Next.js 15 Web Application**:
  - Multi-turn conversational interface with persistent SQLite chat sessions.
  - Interactive source citation drawer showing chunk excerpts and web links.
  - Real-time LangGraph step badges and progress pill.
  - Document management dashboard with drag-and-drop PDF upload and progress tracking.
- **Advanced Technical Chunking & Noise Cleaning**:
  - Automatic header/footer/page-number noise stripping.
  - `RecursiveCharacterTextSplitter` tuned for code fences, markdown headers, and structured documents.
- **High-Performance LanceDB Vector Store**:
  - Disk-backed Apache Arrow storage with sub-millisecond retrieval.
  - Multi-tenant document isolation by `user_id`.
  - Zero-overhead in-process execution inside Docker without additional container weight.
- **Relational Metadata & Chat Persistence (SQLite)**:
  - Users, documents, chat sessions, and message histories tracked in SQLite.
- **Automated Evaluation Pipeline (Ragas)**:
  - Benchmark measuring Context Precision, Faithfulness, and Answer Relevance.
- **Full Observability (Prometheus & Grafana)**:
  - FastAPI metrics exposed on `/metrics`.
  - Grafana dashboard tracking QPS, p95 latency, RAG route decisions, grader pass rates, and ingestion throughput.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons |
| **Backend API** | FastAPI (Python 3.11/3.13), Uvicorn, Pydantic |
| **Orchestration** | LangGraph (v0.2+), LangChain (v0.3+) |
| **LLM Provider** | Google Gemini (Gemini 2.5 Flash / 2.0 Flash) via `ChatGoogleGenerativeAI` |
| **Vector Store** | LanceDB (Embedded Apache Arrow) |
| **Relational DB** | SQLite (SQLAlchemy 2.0) |
| **Web Search** | Tavily Search API |
| **Evaluation** | Ragas (Context Precision, Faithfulness, Answer Relevance), HuggingFace Datasets |
| **Monitoring** | Prometheus, Grafana |
| **DevOps** | Docker, Podman Compose, Nginx SSL, GitHub Actions CI/CD |

---

## Quick Start

### 1. Environment Variables

Create or update your `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
RAG_SECRET_KEY=your_jwt_secret_key
TAVILY_API_KEY=your_tavily_api_key  # Optional: for live web search fallback
```

### 2. Local Development

#### Backend (FastAPI):
```bash
# Install dependencies
uv sync # or pip install -r requirements.txt

# Run FastAPI backend with live reload
uv run uvicorn api:app --reload --port 8000
```

#### Frontend (Next.js):
```bash
cd frontend/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Docker Deployment (Full Stack)

Run the full stack (FastAPI, Next.js, Prometheus, Grafana) with a single command:

```bash
docker compose up -d --build
```

### Service Access:
- **Web Application**: [http://localhost:3000](http://localhost:3000) (or [http://localhost:8501](http://localhost:8501))
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Grafana Dashboards**: [http://localhost:3001](http://localhost:3001) (Credentials: `admin` / `admin`)

---

## Automated Evaluation (Ragas)

To benchmark the RAG pipeline:

```bash
uv run python -m backend.evaluation --output reports/evaluation_results.json
```

Or trigger evaluation via the Web UI under the **Observability & Stats** tab.

---

## License

MIT License. Developed by [Amrit Bhaganagare](https://github.com/Amrit-B/rag-app).
