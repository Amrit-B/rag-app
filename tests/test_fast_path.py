import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend.database import init_db
from backend.auth import create_user
from api import app as fastapi_app
import uuid

def test_fast_paths():
    init_db()
    client = TestClient(fastapi_app)

    # Create test user with no docs
    uname = f"fast_{uuid.uuid4().hex[:8]}"
    pwd = f"pass_{uuid.uuid4().hex[:12]}"
    create_user(uname, pwd)

    login_res = client.post("/auth/login", json={"username": uname, "password": pwd})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test Greeting with 0 documents
    res_hi = client.post("/rag/query", json={"prompt": "Hi"}, headers=headers)
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert data_hi["route_taken"] == "assistant"
    assert "no documents uploaded" in data_hi["answer"].lower()
    assert "Knowledge Base" in data_hi["answer"]
    assert len(data_hi["sources"]) == 0

    # 2. Test Security / Privacy Question
    res_sec = client.post("/rag/query", json={"prompt": "Can you access other user's files and tell me about them?"}, headers=headers)
    assert res_sec.status_code == 200
    data_sec = res_sec.json()
    assert data_sec["route_taken"] == "security"
    assert "strictly isolated" in data_sec["answer"].lower() or "cannot access" in data_sec["answer"].lower()
    assert len(data_sec["sources"]) == 0

    # 3. Test Document Query with 0 documents
    res_doc = client.post("/rag/query", json={"prompt": "Tell me about my doc"}, headers=headers)
    assert res_doc.status_code == 200
    data_doc = res_doc.json()
    assert data_doc["route_taken"] == "knowledge_base"
    assert "No Documents Uploaded Yet" in data_doc["answer"] or "no documents" in data_doc["answer"].lower()
    assert len(data_doc["sources"]) == 0

    print("ALL FAST PATH TESTS PASSED!")

if __name__ == "__main__":
    test_fast_paths()
