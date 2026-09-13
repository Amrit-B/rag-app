from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import asyncio
from uuid import uuid4
import time

from backend.constants import DATA_PATH
from backend import auth
from backend.auth import create_access_token, authenticate_user, get_current_user
from backend.database import (
    init_db,
    db_create_chat_session,
    db_list_chat_sessions,
    db_get_chat_session,
    db_delete_chat_session,
    db_add_chat_message,
    db_get_chat_messages,
)
from backend.document_service import (
    ingest_single_document,
    list_documents,
    delete_document,
    reset_knowledge_base,
)
from backend.data_models import (
    Prompt,
    RegisterModel,
    LoginModel,
    RAGQueryResponse,
    CitationSource,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    DocumentMetadataResponse,
    UploadJobResponse,
)
from backend.graph import app as rag_graph
from backend.metrics import (
    setup_metrics,
    RAG_QUERIES_TOTAL,
    RAG_INGESTION_TOTAL,
    RAG_INGESTION_DURATION_SECONDS,
    RAG_GRADER_DECISIONS_TOTAL,
    RAG_HALLUCINATION_DECISIONS_TOTAL,
    RAG_WEB_SEARCHES_TOTAL,
)

MAX_UPLOAD_MB = 200
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

app = FastAPI(
    title="Agentic RAG API",
    description="Enterprise RAG API powered by LangGraph, LanceDB, Tavily, and SQLite",
    version="2.0.0",
)

# Prometheus metrics instrumentation (/metrics)
setup_metrics(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion_semaphore = asyncio.Semaphore(2)
ingestion_jobs: dict[str, dict] = {}


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Agentic RAG API is running",
        "engine": "LangGraph + LanceDB + SQLite",
    }


# ==========================================
# Authentication Endpoints
# ==========================================

@app.post("/auth/register")
async def register_user(payload: RegisterModel):
    user = auth.create_user(payload.username, payload.password)
    return {"status": "success", "user": user}


@app.post("/auth/login")
async def login(payload: LoginModel):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"id": user["id"], "username": user["username"]})
    return {"access_token": token, "username": user["username"], "user_id": str(user["id"])}


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}


# ==========================================
# Chat Sessions & History Endpoints
# ==========================================

@app.post("/api/sessions", response_model=ChatSessionResponse)
async def create_session(payload: ChatSessionCreate, current_user: dict = Depends(get_current_user)):
    session = db_create_chat_session(user_id=str(current_user["id"]), title=payload.title or "New Conversation")
    return session


@app.get("/api/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    return db_list_chat_sessions(user_id=str(current_user["id"]))


@app.get("/api/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    return db_get_chat_messages(session_id=session_id, user_id=str(current_user["id"]))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    success = db_delete_chat_session(session_id=session_id, user_id=str(current_user["id"]))
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "message": "Session deleted"}


# ==========================================
# Agentic RAG Query Endpoint (LangGraph)
# ==========================================

@app.post("/rag/query", response_model=RAGQueryResponse)
async def query_documentation(query: Prompt, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["id"])
        session_id = query.session_id

        # Auto-create session if not provided
        if not session_id:
            new_session = db_create_chat_session(user_id=user_id, title="New Conversation")
            session_id = new_session["id"]

        # Save user message to SQLite
        db_add_chat_message(
            session_id=session_id,
            sender="user",
            content=query.prompt,
        )

        # Execute LangGraph Multi-Step Workflow
        initial_state = {
            "question": query.prompt,
            "generation": None,
            "web_search": False,
            "documents": [],
            "user_id": user_id,
            "loop_step": 0,
            "sources": [],
            "route_taken": "vectorstore",
        }

        result = await asyncio.to_thread(rag_graph.invoke, initial_state)

        answer = result.get("generation") or "No answer produced by RAG pipeline."
        route_taken = result.get("route_taken") or "vectorstore"
        raw_sources = result.get("sources") or []

        # Record metrics
        RAG_QUERIES_TOTAL.labels(route_taken=route_taken).inc()
        if result.get("web_search"):
            RAG_WEB_SEARCHES_TOTAL.labels(status="triggered").inc()

        # Build citation sources
        structured_sources = []
        filepath_list = []
        for s in raw_sources:
            structured_sources.append(
                CitationSource(
                    source=s.get("source", "Document"),
                    snippet=s.get("snippet", ""),
                    source_type=s.get("source_type", "document"),
                    url=s.get("url"),
                )
            )
            filepath_list.append(s.get("source", "Document"))

        # Save assistant message to SQLite
        db_add_chat_message(
            session_id=session_id,
            sender="assistant",
            content=answer,
            sources=[s.dict() for s in structured_sources],
            route_taken=route_taken,
        )

        return RAGQueryResponse(
            answer=answer,
            filepath=", ".join(list(dict.fromkeys(filepath_list))),
            sources=structured_sources,
            route_taken=route_taken,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


# ==========================================
# Document Ingestion & Management
# ==========================================

def _set_job_status(job_id: str, status: str, error: str | None = None) -> None:
    job = ingestion_jobs.get(job_id)
    if not job:
        return
    job["status"] = status
    job["error"] = error


async def process_document_background(pdf_path: Path, owner_id: str, job_id: str):
    async with ingestion_semaphore:
        start_time = time.time()
        try:
            _set_job_status(job_id, "processing")
            result = await asyncio.to_thread(ingest_single_document, pdf_path, owner_id)
            duration = time.time() - start_time
            RAG_INGESTION_DURATION_SECONDS.observe(duration)

            if result.get("success"):
                _set_job_status(job_id, "completed")
                RAG_INGESTION_TOTAL.labels(status="success").inc()
            else:
                _set_job_status(job_id, "failed", result.get("error") or result.get("message"))
                RAG_INGESTION_TOTAL.labels(status="failed").inc()
        except Exception as e:
            _set_job_status(job_id, "failed", str(e))
            RAG_INGESTION_TOTAL.labels(status="failed").inc()
            print(f"Error processing {pdf_path.name}: {e}")


def _save_upload_file(src_file, dest_path: Path) -> None:
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(src_file, buffer)


@app.post("/rag/upload", response_model=UploadJobResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # pyrefly: ignore [missing-attribute]
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_size_bytes = None
    try:
        file.file.seek(0, 2)
        file_size_bytes = file.file.tell()
        file.file.seek(0)
    except Exception:
        file_size_bytes = None

    if file_size_bytes is not None and file_size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max upload size is {MAX_UPLOAD_MB}MB",
        )

    user_dir = DATA_PATH / current_user["username"]
    user_dir.mkdir(parents=True, exist_ok=True)
    # pyrefly: ignore [bad-argument-type]
    pdf_path = user_dir / Path(file.filename).name

    try:
        await asyncio.to_thread(_save_upload_file, file.file, pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")
    finally:
        file.file.close()

    job_id = str(uuid4())
    ingestion_jobs[job_id] = {
        "owner_id": str(current_user["id"]),
        "filename": file.filename,
        "status": "queued",
        "error": None,
    }

    background_tasks.add_task(process_document_background, pdf_path, str(current_user["id"]), job_id)

    return UploadJobResponse(
        job_id=job_id,
        # pyrefly: ignore [bad-argument-type]
        filename=file.filename,
        status="queued",
    )


@app.get("/rag/upload-status/{job_id}", response_model=UploadJobResponse)
async def get_upload_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = ingestion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if str(job.get("owner_id")) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Forbidden")

    return UploadJobResponse(
        job_id=job_id,
        # pyrefly: ignore [bad-argument-type]
        filename=job.get("filename"),
        # pyrefly: ignore [bad-argument-type]
        status=job.get("status"),
        error=job.get("error"),
    )


@app.get("/rag/documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    docs = list_documents(owner_id=str(current_user["id"]))
    return {"documents": docs}


@app.delete("/rag/documents/{doc_id}")
async def remove_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    result = delete_document(doc_id, owner_id=str(current_user["id"]))
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("message"))


@app.post("/rag/reset")
async def reset_database(current_user: dict = Depends(get_current_user)):
    result = reset_knowledge_base(owner_id=str(current_user["id"]))
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("message"))


# ==========================================
# Ragas Automated Evaluation Endpoint
# ==========================================

@app.post("/admin/evaluate")
async def trigger_evaluation(current_user: dict = Depends(get_current_user)):
    try:
        from backend.evaluation import run_evaluation
        report = await asyncio.to_thread(run_evaluation, user_id=str(current_user["id"]))
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
