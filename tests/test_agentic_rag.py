import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from backend.database import (
    init_db,
    db_save_document,
    db_list_documents,
    db_get_document,
    db_delete_document,
    db_create_chat_session,
    db_list_chat_sessions,
    db_add_chat_message,
    db_get_chat_messages,
)
from backend.preprocessor import clean_text
from backend.document_service import get_technical_text_splitter, get_vector_db_table
from backend.graph.consts import RETRIEVE, GRADE_DOCUMENTS, GENERATE, WEBSEARCH
from backend.graph import app as rag_graph
from api import app as fastapi_app


def test_database_and_metadata():
    init_db()
    # Test document metadata
    doc = db_save_document(
        doc_id="test_doc_1",
        owner_id="test_user_99",
        filename="manual.pdf",
        filepath="/data/manual.pdf",
        file_size_bytes=10240,
        chunk_count=5,
        status="completed",
    )
    assert doc["doc_id"] == "test_doc_1"
    assert doc["chunk_count"] == 5

    docs = db_list_documents(owner_id="test_user_99")
    assert len(docs) >= 1
    assert any(d["doc_id"] == "test_doc_1" for d in docs)

    fetched = db_get_document("test_doc_1", "test_user_99")
    assert fetched is not None
    assert fetched["filename"] == "manual.pdf"

    # Test Chat Sessions & Messages
    session = db_create_chat_session(user_id="test_user_99", title="Test Chat")
    assert session["id"] is not None

    msg = db_add_chat_message(
        session_id=session["id"],
        sender="user",
        content="What is the architecture?",
    )
    assert msg["sender"] == "user"

    msgs = db_get_chat_messages(session_id=session["id"], user_id="test_user_99")
    assert len(msgs) >= 1
    assert msgs[-1]["content"] == "What is the architecture?"

    # Cleanup test document
    db_delete_document("test_doc_1", "test_user_99")


def test_text_cleaner():
    raw = (
        "Page 1 of 10\n"
        "Confidential - For internal use only\n"
        "This is an extra-\nordinary architec-\nture doc.\n"
        "Page 2 of 10"
    )
    cleaned = clean_text(raw)
    assert "Page 1 of 10" not in cleaned
    assert "Confidential" not in cleaned
    assert "extraordinary" in cleaned
    assert "architecture" in cleaned


def test_technical_splitter():
    splitter = get_technical_text_splitter(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "# Overview\n\n"
        "Here is the system architecture with code:\n"
        "```python\ndef run():\n    return True\n```\n\n"
        "End of technical summary."
    )
    chunks = splitter.split_text(sample_text)
    assert len(chunks) >= 1
    assert any("```python" in c for c in chunks)


def test_lancedb_table():
    table = get_vector_db_table()
    assert table is not None


def test_graph_nodes_defined():
    # Verify LangGraph nodes and compilation
    assert rag_graph is not None
    nodes = rag_graph.nodes
    assert RETRIEVE in nodes
    assert GRADE_DOCUMENTS in nodes
    assert GENERATE in nodes
    assert WEBSEARCH in nodes


def test_fastapi_endpoints():
    client = TestClient(fastapi_app)
    # Root
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Prometheus metrics
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    assert b"rag_queries_total" in res_metrics.content or b"process_virtual_memory_bytes" in res_metrics.content


def test_auth_and_admin_validation():
    init_db()
    client = TestClient(fastapi_app)

    # 1. Test registration with username < 3 chars -> rejected
    import uuid
    dummy_pass = f"p_{uuid.uuid4().hex[:12]}"
    res = client.post("/auth/register", json={"username": "ab", "password": dummy_pass})
    assert res.status_code in [400, 422]

    # 2. Test registration with password < 6 chars -> rejected
    res = client.post("/auth/register", json={"username": "validuser", "password": "12"})
    assert res.status_code in [400, 422]

    # 3. Successful registration with valid credentials
    test_user = f"user_{uuid.uuid4().hex[:8]}"
    test_pass = f"pass_{uuid.uuid4().hex[:12]}"
    res = client.post("/auth/register", json={"username": test_user, "password": test_pass})
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # 4. Login as regular user -> is_admin is False
    res_login = client.post("/auth/login", json={"username": test_user, "password": test_pass})
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert login_data["is_admin"] is False
    token = login_data["access_token"]

    # 5. Regular user accessing /admin/evaluate -> 403 Forbidden
    res_eval = client.post("/admin/evaluate", headers={"Authorization": f"Bearer {token}"})
    assert res_eval.status_code == 403

    # 6. Admin user creation and verification
    from backend.auth import create_user
    admin_uname = f"adm_{uuid.uuid4().hex[:8]}"
    admin_pwd = f"pass_{uuid.uuid4().hex[:12]}"
    create_user(admin_uname, admin_pwd, is_admin=True)
    res_admin = client.post("/auth/login", json={"username": admin_uname, "password": admin_pwd})
    assert res_admin.status_code == 200
    assert res_admin.json()["is_admin"] is True


if __name__ == "__main__":
    print("Running integration tests...")
    test_database_and_metadata()
    print("[PASS] test_database_and_metadata passed")
    test_auth_and_admin_validation()
    print("[PASS] test_auth_and_admin_validation passed")
    test_text_cleaner()
    print("[PASS] test_text_cleaner passed")
    test_technical_splitter()
    print("[PASS] test_technical_splitter passed")
    test_lancedb_table()
    print("[PASS] test_lancedb_table passed")
    test_graph_nodes_defined()
    print("[PASS] test_graph_nodes_defined passed")
    test_fastapi_endpoints()
    print("[PASS] test_fastapi_endpoints passed")
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

