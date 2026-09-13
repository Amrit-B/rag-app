from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import asyncio
from uuid import uuid4
import time
import re

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
    LoginResponse,
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


@app.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginModel):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({
        "id": user["id"],
        "username": user["username"],
        "is_admin": user.get("is_admin", False),
    })
    return {
        "access_token": token,
        "username": user["username"],
        "user_id": str(user["id"]),
        "is_admin": user.get("is_admin", False),
    }


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

        # Fast-Path Evaluation for Greetings, System Privacy, and 0-Document State
        prompt_trimmed = query.prompt.strip()
        user_docs = list_documents(owner_id=user_id)
        doc_count = len(user_docs)

        fast_answer = None
        fast_route = None

        # 1. Privacy / Multi-Tenant Isolation Questions
        if re.search(r"\b(access|see|view|read|share)\s+(other|another|anyone else's)\s*(user|users|people|person)?'?s?\s*(file|files|doc|docs|document|documents|data)\b", prompt_trimmed, re.IGNORECASE) or \
           re.search(r"\b(can you access other user|can other users see my|is my (?:uploaded\s+)?(?:data|file|files|document|documents|content)?\s*(?:private|isolated|secure))\b", prompt_trimmed, re.IGNORECASE):
            fast_answer = (
                "### 🔒 Strict Multi-Tenant Isolation & Privacy\n\n"
                "**No. I cannot access, search, or view documents uploaded by other users, and other users cannot access yours.**\n\n"
                "- **Partitioned Storage**: Every document chunk in LanceDB is indexed with your unique `owner_id`.\n"
                "- **Isolated Vector Retrieval**: All vector similarity queries enforce `owner_id = '{user_id}'` at the database level.\n"
                "- **Session Privacy**: Chat histories and metadata are partitioned in SQLite by your user credentials."
            )
            fast_route = "security"

        # 2. Conversational Greetings, Onboarding & Introductions
        elif re.search(r"^(hi|hello|hey|greetings|howdy|good\s+(morning|afternoon|evening)|sup|what'?s\s+up)[\s!.,?]*$", prompt_trimmed, re.IGNORECASE) or \
             re.search(r"^(who are you|what can you do|what is this( app| project)?|help|how to get started)[\s!.,?]*$", prompt_trimmed, re.IGNORECASE) or \
             re.search(r"\b(how (do|can) i (get started|upload|start|use this)|how to upload)\b", prompt_trimmed, re.IGNORECASE):
            if doc_count == 0:
                fast_answer = (
                    "### Welcome to the Agentic Self-Reflective RAG Assistant! 👋\n\n"
                    "I am powered by **LangGraph**, **LanceDB**, and **Gemini 2.5 Flash**, designed to provide grounded, citation-backed answers without hallucinations.\n\n"
                    "📁 **Knowledge Base Status**: You currently have **no documents uploaded**.\n\n"
                    "**To get started with document Q&A:**\n"
                    "1. Click the **Knowledge Base** tab in the sidebar.\n"
                    "2. Upload your PDF files (lecture slides, research papers, reports, manuals).\n"
                    "3. Return to this chat to ask questions—I will retrieve relevant passages, grade relevance, and provide precise citations.\n\n"
                    "💡 *You can also ask broad or current world questions right now, and I will use live Tavily web search to answer!*"
                )
            else:
                doc_names = ", ".join([d.get("filename", "Document") for d in user_docs[:3]])
                extra = f" (and {doc_count - 3} more)" if doc_count > 3 else ""
                fast_answer = (
                    f"### Hello! How can I assist you today? 👋\n\n"
                    f"📁 **Knowledge Base Ready**: You have **{doc_count} document{'s' if doc_count != 1 else ''}** indexed (`{doc_names}{extra}`).\n\n"
                    f"You can ask me to:\n"
                    f"- Summarize key findings or specific sections\n"
                    f"- Extract data points, metrics, or technical requirements\n"
                    f"- Cross-reference your documents with live web search\n\n"
                    f"What would you like to explore?"
                )
            fast_route = "assistant"

        # 3. Document Query with Zero Uploads
        elif doc_count == 0 and (
            re.search(r"\b(my\s+doc|my\s+file|uploaded\s+doc|uploaded\s+file|the\s+doc|the\s+pdf|in\s+my\s+documents?)\b", prompt_trimmed, re.IGNORECASE) or
            re.search(r"^(summarize|what is in|tell me about|explain)\s+(the|my)\s+(doc|docs|document|documents|file|files|pdf)[\s!.,?]*$", prompt_trimmed, re.IGNORECASE)
        ):
            fast_answer = (
                "### ⚠️ No Documents Uploaded Yet\n\n"
                "I couldn't find any documents in your Knowledge Base to answer this question.\n\n"
                "**Next Steps:**\n"
                "1. Head to the **Knowledge Base** tab in the left sidebar.\n"
                "2. Upload a PDF file to index it into LanceDB.\n"
                "3. Return to this chat to ask questions grounded in your document's content!"
            )
            fast_route = "knowledge_base"

        # 4. Pipeline Architecture & Hallucination Prevention
        elif re.search(r"\b(how does (?:this|the) (?:agentic\s+)?(?:pipeline|system|agent|rag|app)|prevent(?:ing)? hallucination|avoid(?:ing)? hallucination|how (?:is|are) hallucination(?:s)? (?:prevented|avoided|handled))\b", prompt_trimmed, re.IGNORECASE):
            fast_answer = (
                "### 🛡️ How This Agentic RAG Pipeline Prevents Hallucinations\n\n"
                "Unlike standard naive RAG (which blindly dumps raw vector search results into an LLM), this system uses a **Self-Reflective LangGraph Architecture**:\n\n"
                "1. **Batch Document Relevance Grading**: Every candidate chunk retrieved from LanceDB is evaluated for relevance. Off-topic chunks are automatically pruned.\n"
                "2. **Hallucination Grader**: After the response is drafted, a dedicated evaluator verifies that every statement is strictly supported by the retrieved source context.\n"
                "3. **Self-Correction & Web Fallback**: If the drafted answer is not grounded or the documents lack sufficient facts, the agent triggers **Tavily live web search** to fill gaps.\n"
                "4. **Grounded Citations**: Every claim in the final answer is cited with verifiable chunk IDs and filenames."
            )
            fast_route = "assistant"
        # 5. Supported Document Formats & Ingestion Details
        elif re.search(r"\b(what (?:document|file)?\s*formats?|what can i upload|what (?:kind of\s+)?(?:documents?|files?|content) (?:can i|to) upload|supported (?:file|document)?\s*formats?)\b", prompt_trimmed, re.IGNORECASE):
            fast_answer = (
                "### 📄 Supported Document Formats & Vector Indexing\n\n"
                "- **Supported File Format**: PDF documents (`.pdf`) up to 200 MB (technical reports, research papers, manuals, lecture slides, architecture guides).\n"
                "- **Text Cleaning**: Automated header/footer stripping, page artifact filtering, and hyphenation de-wrapping.\n"
                "- **Technical Chunking**: Structured splitting using `RecursiveCharacterTextSplitter` preserving code fences (```), Markdown headers (`#`, `##`), and bullet lists.\n"
                "- **Vector Embeddings**: Real-time batch vectorization via **768-dimensional Gemini embeddings** stored in high-performance **LanceDB** for sub-millisecond retrieval."
            )
            fast_route = "knowledge_base"

        # If fast-path matched, save and return immediately (0 LLM / Tavily calls wasted!)
        if fast_answer:
            RAG_QUERIES_TOTAL.labels(route_taken=fast_route).inc()
            db_add_chat_message(
                session_id=session_id,
                sender="assistant",
                content=fast_answer,
                sources=[],
                route_taken=fast_route,
            )
            return RAGQueryResponse(
                answer=fast_answer,
                filepath="",
                sources=[],
                route_taken=fast_route,
                session_id=session_id,
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
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required to trigger evaluation benchmarks")
    try:
        from backend.evaluation import run_evaluation
        report = await asyncio.to_thread(run_evaluation, user_id=str(current_user["id"]))
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
