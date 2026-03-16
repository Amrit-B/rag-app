FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for sentence-transformers and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first for image size reduction
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Inject Google Analytics into Streamlit's native index.html
RUN sed -i "s@<head>@<head><script async src='https://www.googletagmanager.com/gtag/js?id=G-4WVG826P17'></script><script>window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag('js', new Date()); gtag('config', 'G-4WVG826P17');</script>@g" /usr/local/lib/python3.11/site-packages/streamlit/static/index.html
# Set PYTHONPATH to ensure backend module is found without __init__.py
ENV PYTHONPATH=/app

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]