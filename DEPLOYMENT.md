# Agentic RAG Platform - Deployment Guide

This guide covers running the application locally, containerized with Docker / Podman, and deploying to an Oracle Cloud VM using automated GitHub Actions CI/CD.

---

## 1. Local Development

### Prerequisites
- Python 3.11+ (or uv)
- Node.js 20+ & npm

### Setup
1. Clone the repository and configure `.env`:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   RAG_SECRET_KEY=your_jwt_secret
   TAVILY_API_KEY=your_tavily_api_key  # Optional for live web search
   ```

2. Start the FastAPI Backend:
   ```bash
   uv sync
   uv run uvicorn api:app --reload --port 8000
   ```

3. Start the Next.js Frontend:
   ```bash
   cd frontend/web
   npm install
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000).

---

## 2. Local Docker Stack Testing

Build and run the entire 4-container stack (Backend, Frontend, Prometheus, Grafana):

```bash
docker compose up -d --build
```

### Services Overview:
| Service | Internal Port | Host Port | Description |
| :--- | :--- | :--- | :--- |
| `fastapi` | 8000 | 8000 | LangGraph agentic RAG backend & SQLite |
| `frontend` | 3000 | 3000, 8501 | Modern Next.js 15 Tailwind UI |
| `prometheus` | 9090 | 9090 | Scrapes `/metrics` every 5 seconds |
| `grafana` | 3000 | 3001 | Preconfigured metrics dashboard |

- Web Application: http://localhost:3000 (or http://localhost:8501)
- Backend Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (User: `admin`, Pass: `admin`)

---

## 3. Automated CI/CD Deployment (GitHub Actions)

The workflow (`.github/workflows/deploy.yml`) handles continuous integration and deployment automatically on push to `main`:

1. **Build & Push**:
   - Builds `ambro333/rag-api:latest` (from root `Dockerfile`)
   - Builds `ambro333/rag-frontend:latest` (from `frontend/web/Dockerfile`)
   - Pushes both images to Docker Hub.
2. **Deploy via SSH**:
   - Connects to your Oracle Cloud VM.
   - Pulls latest container images.
   - Restarts containers using `podman-compose` / `docker-compose`.
   - Reloads Nginx reverse proxy.

### Required GitHub Secrets:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub token
- `VM_HOST`: VM public IP address
- `VM_USER`: SSH username (e.g., `opc`)
- `VM_SSH_KEY`: SSH private key
- `VM_SSH_PORT`: SSH port (default: 22)
- `VM_APP_PATH`: Deployment path (e.g., `~/rag_app`)

---

## 4. Nginx SSL Reverse Proxy

The configuration in `backup_nginx/conf.d/amritb.me.conf` maps traffic under HTTPS:
- `/` -> Next.js frontend (`http://localhost:8501` or `http://localhost:3000`)
- `/api/` -> FastAPI backend (`http://localhost:8000/`)
- `/auth/`, `/rag/` -> FastAPI backend direct endpoints

Restart Nginx on the VM:
```bash
sudo nginx -t && sudo systemctl restart nginx
```
