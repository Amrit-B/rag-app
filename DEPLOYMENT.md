# RAG Application - Deployment Guide

## Local Development

1. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set environment variables in `.env`:
```
GOOGLE_API_KEY=your_api_key_here
RAG_SECRET_KEY=your_secret_key
```

3. Run locally:
```bash
# Terminal 1 - FastAPI
python -m uvicorn api:app --reload

# Terminal 2 - Streamlit
streamlit run frontend/app.py
```

## Local Docker Testing

Build and test with Docker:
```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:8501
- API: http://localhost:8000

## Automated CI/CD Deployment

This application uses **GitHub Actions for automatic deployment**.

### How It Works

1. **Push to main branch** triggers GitHub Actions workflow
2. **Docker image** is built and pushed to Docker Hub (`ambro333/rag-app:latest`)
3. **SSH connection** to Oracle Cloud VM executes deployment script
4. **Containers** are pulled and restarted with latest image
5. **Nginx** reverse proxy with SSL serves the application

### Prerequisites

Before first deployment, ensure:

1. **GitHub Secrets configured** (in repository settings):
   - `DOCKER_USERNAME` - Docker Hub username
   - `DOCKER_PASSWORD` - Docker Hub access token
   - `VM_HOST` - Oracle Cloud VM public IP
   - `VM_USER` - SSH username (e.g., `opc`)
   - `VM_SSH_KEY` - Private SSH key
   - `VM_SSH_PORT` - SSH port (default: 22)
   - `VM_APP_PATH` - App directory on VM (e.g., `~/rag_app`)

2. **VM Setup** (one-time):
   ```bash
   ssh -i <your-key> opc@<vm-ip>
   
   # Install podman and podman-compose
   sudo dnf install -y podman podman-compose
   
   # Clone repository
   git clone <repo-url> ~/rag_app
   cd ~/rag_app
   
   # Create .env file with secrets
   cat > .env << EOF
   GOOGLE_API_KEY=your_api_key
   RAG_SECRET_KEY=your_secret_key
   EOF
   ```

3. **Nginx Configuration** (one-time):
   - SSL certificate setup with Let's Encrypt
   - Reverse proxy to container ports (8000, 8501)

### Deployment Workflow

The workflow (`.github/workflows/deploy.yml`) automatically:
1. Builds multi-stage Docker image
2. Pushes to Docker Hub as `ambro333/rag-app:latest`
3. SSH into VM and runs:
   ```bash
   sudo podman pull docker.io/ambro333/rag-app:latest
   sudo /usr/local/bin/podman-compose pull
   sudo /usr/local/bin/podman-compose up -d --remove-orphans
   ```
4. Containers restart with new image

### Manual Deployment (if needed)

If automated deployment fails, deploy manually:

```bash
ssh -i /path/to/key opc@<vm-ip>
cd ~/rag_app

# Pull latest image and restart
sudo podman pull docker.io/ambro333/rag-app:latest
sudo /usr/local/bin/podman-compose down
sudo /usr/local/bin/podman-compose up -d

# Check status
sudo podman ps
```

### Viewing Logs

**On VM:**
```bash
# FastAPI backend
sudo podman logs rag-api -f

# Streamlit frontend
sudo podman logs rag-frontend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Troubleshooting

**Old images still running:**
```bash
# Remove old local images
sudo podman rmi docker.io/ambro333/rag-app:latest 2>&1 || true

# Restart containers
sudo /usr/local/bin/podman-compose down
sudo /usr/local/bin/podman-compose up -d
```

**Container won't start:**
```bash
# Check logs for errors
sudo podman logs <container-name>

# Verify environment variables
cat ~/rag_app/.env
```

## Application Access

- **Frontend**: https://amritb.me (via Nginx SSL)
- **API**: https://amritb.me/api (backend running in container)
- **Local development**: http://localhost:8501 (Streamlit)

## Environment Variables

Required:
- `GOOGLE_API_KEY` - Your Google API key for Gemini

## Monitoring

Check logs:
```bash
docker-compose logs -f
```

Restart services:
```bash
docker-compose restart
```

Stop services:
```bash
docker-compose down
```
