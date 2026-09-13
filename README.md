# Agentic RAG Platform with LangGraph, LanceDB & Next.js

An enterprise-grade, self-reflective Retrieval-Augmented Generation (RAG) platform featuring **LangGraph control flow**, **high-performance Gemini 768-dim embeddings**, **LanceDB vector storage**, **SQLite persistence**, **Tavily live web search fallback**, **Ragas automated evaluation**, and **Prometheus/Grafana observability**.

Based on the self-reflective agentic RAG pattern ([emarco177/langgraph-course](https://github.com/emarco177/langgraph-course/tree/project/agentic-rag)).

---

## Key Features

### 1. Self-Reflective Multi-Step RAG (LangGraph)
- **Question Router Chain**: Intelligently routes queries to vector retrieval, live web search, or instant fast-paths.
- **Batch Document Relevance Grader**: Evaluates candidate chunks in a **single batch API call** rather than serial loops, cutting retrieval latency by **>80%**.
- **Hallucination Verification Node**: Validates that every claim in the drafted response is grounded strictly in retrieved context.
- **Adaptive Web Fallback (Tavily)**: Automatically searches the live web when uploaded documents lack recent context or complete answers.
- **Answer Relevance Grader**: Validates that the synthesized response directly addresses the user's intent.

### 2. High-Performance Vector Search (Gemini & LanceDB)
- **Gemini Embeddings (`models/gemini-embedding-001`)**: Integrated via Google's `genai` SDK using Matryoshka Representation Learning (MRL) at **768 dimensions**.
- **Lightning-Fast Ingestion**: Multi-page PDF ingestion benchmarked at **~2.15 seconds** (down from 45s+ on CPU-bound local models).
- **Embedded LanceDB Table**: Sub-millisecond similarity search backed by Apache Arrow with automated schema dimension migration.
- **Multi-Tenant Scoping**: All vector searches strictly enforce `owner_id` isolation at the database query level.

### 3. Fast-Path Intent Routing (Zero-Token Latency)
- **<2ms Instant Responses**: Intercepts greetings, system architecture/hallucination inquiries, supported document formats, and zero-document queries without making external LLM or search calls.
- **Guaranteed Consistency**: Provides deterministic, structured onboarding and privacy assurances to users.

### 4. Modern Next.js 15 Web Application
- **Clean Markdown Rendering**: Powered by `react-markdown` with syntax styling, headers, tables, and distinct bullet points (no raw `#` or `*` tokens).
- **Dynamic Knowledge Base Status Banner**: Real-time alerts guiding users to upload files when the knowledge base is empty.
- **Tab Persistence**: Upload jobs, polling intervals, and UI states persist in memory when navigating between Chat, Knowledge Base, and About tabs.
- **Upload Concurrency Guard**: Locks file dropzone during active ingestion to prevent race conditions.
- **Multi-Turn Chat Sessions**: Persistent conversation history with session naming and deletion backed by SQLite.
- **Interactive Citation Drawer**: Chunk excerpts, filenames, and live web sources for every cited claim.

### 5. Enterprise Observability & DevOps
- **Prometheus Metrics**: FastAPI metrics exposed at `/metrics` tracking QPS, p95 latency, RAG route decisions, and grader pass rates.
- **Grafana Dashboards**: Visualizes system performance, vector retrieval times, and LLM throughput.
- **CI/CD Automation**: GitHub Actions pipeline building Docker containers and deploying directly to production.

### 6. Model Context Protocol (MCP) Integration
- **Prometheus MCP (`mcp-prometheus`)**: Real-time PromQL querying, resource bottleneck diagnosis, and metric inspection for AI agents.
- **SQLite MCP (`mcp-server-sqlite`)**: Direct database schema inspection and metadata querying for `auth.db`.
- **Docker MCP (`mcp-server-docker`)**: Automated container lifecycle management and logs inspection.
- **Tavily MCP (`@agtools/mcp-tavily`)**: Standardized web search tool invocation conforming to the Model Context Protocol.
- **LangChain MCP (`docs-langchain`, `reference-langchain`)**: Embedded documentation and API symbol lookups for agent development.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, ReactMarkdown |
| **Backend API** | FastAPI (Python 3.11/3.13), Uvicorn, Pydantic |
| **Orchestration** | LangGraph (v0.2+), LangChain (v0.3+) |
| **LLM & Embeddings** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) & Gemini Embeddings (`models/gemini-embedding-001`, 768-dim) |
| **Vector Store** | LanceDB (Embedded Apache Arrow) |
| **Relational DB** | SQLite (SQLAlchemy 2.0) |
| **Web Search** | Tavily Search API |
| **Agent Protocol** | Model Context Protocol (MCP) (Prometheus, SQLite, Docker, Tavily, LangChain Docs) |
| **Evaluation** | Ragas (Context Precision, Faithfulness, Answer Relevance), HuggingFace Datasets |
| **Monitoring** | Prometheus, Grafana |
| **DevOps** | Docker, Docker Compose, Nginx SSL, GitHub Actions CI/CD |

---

## Quick Start

### 1. Environment Variables

Create or update your `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
RAG_SECRET_KEY=your_jwt_secret_key
TAVILY_API_KEY=your_tavily_api_key  # For live web search fallback
```

### 2. Local Development

#### Backend (FastAPI):
```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend with live reload
uvicorn api:app --reload --port 8000
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
- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Grafana Dashboards**: [http://localhost:3001](http://localhost:3001)

---

## Automated Testing & Evaluation

### 1. Fast-Path & Integration Tests
```bash
python -u tests/test_fast_path.py
python -u tests/test_agentic_rag.py
```

### 2. Automated RAG Evaluation (Ragas)
```bash
python -m backend.evaluation --output reports/evaluation_results.json
```
Benchmark scores (Context Precision, Faithfulness, Answer Relevance) are also accessible directly in the Web UI under the **Observability & Stats** tab.

---

## Model Context Protocol (MCP) Configuration

This platform integrates with the open **Model Context Protocol (MCP)** standard, enabling autonomous agents and AI development environments to inspect, query, and operate the entire system stack:

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "npx",
      "args": ["-y", "mcp-prometheus@latest"],
      "env": { "PROMETHEUS_URL": "http://localhost:9090" }
    },
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./data/auth.db"]
    },
    "docker": {
      "command": "uvx",
      "args": ["mcp-server-docker"]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "@agtools/mcp-tavily"],
      "env": { "TAVILY_API_KEY": "your_tavily_api_key" }
    },
    "docs-langchain": {
      "serverUrl": "https://docs.langchain.com/mcp"
    }
  }
}
```

---

## Author & Contact

Developed by **Amrit Bhaganagare**  
- **GitHub**: [Amrit-B](https://github.com/Amrit-B/rag-app)  
- **LinkedIn**: [amritb08](https://www.linkedin.com/in/amritb08/)

## License

MIT License.
