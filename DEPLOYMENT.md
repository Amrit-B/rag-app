# RAG Application - Oracle Cloud Deployment

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables in `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

3. Run locally:
```bash
# Terminal 1 - FastAPI
uvicorn api:app --reload

# Terminal 2 - Streamlit
streamlit run frontend/app.py
```

## Docker Deployment

### Build and run locally:
```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:8501
- API: http://localhost:8000

### Deploy to Oracle Cloud

#### Prerequisites:
- Oracle Cloud account
- Docker installed locally
- Oracle CLI (OCI) configured

#### Steps:

1. **Create Compute Instance:**
   - Login to Oracle Cloud Console
   - Navigate to Compute > Instances
   - Create instance (Ubuntu 22.04, minimum 2 OCPU, 8GB RAM)
   - Open ports: 8000 (API), 8501 (Frontend), 22 (SSH)

2. **SSH into instance:**
```bash
ssh -i <your-key.pem> ubuntu@<instance-ip>
```

3. **Install Docker on instance:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

4. **Clone your repository:**
```bash
git clone <your-repo-url>
cd RAG
```

5. **Create .env file:**
```bash
echo "GOOGLE_API_KEY=your_key_here" > .env
```

6. **Run with Docker Compose:**
```bash
docker-compose up -d
```

7. **Configure Security List (Oracle Cloud Console):**
   - Go to Networking > Virtual Cloud Networks
   - Select your VCN > Security Lists
   - Add Ingress Rules:
     - Port 8000 (API)
     - Port 8501 (Frontend)

8. **Access your app:**
   - Frontend: http://<instance-ip>:8501
   - API: http://<instance-ip>:8000

#### Optional: Use Oracle Container Registry

1. **Tag and push image:**
```bash
docker tag rag-api <region>.ocir.io/<tenancy-namespace>/rag-api:latest
docker push <region>.ocir.io/<tenancy-namespace>/rag-api:latest
```

2. **Deploy from registry on compute instance**

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
