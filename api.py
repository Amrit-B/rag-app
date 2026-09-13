from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.rag import rag_agent
from backend.data_models import Prompt
from backend.document_service import ingest_single_document, list_documents, delete_document, reset_knowledge_base
from backend.constants import DATA_PATH, VECTOR_DATABASE_PATH
from backend import auth
from backend.auth import init_db, create_access_token, authenticate_user, get_current_user
from pathlib import Path
import shutil
import lancedb
import asyncio
from uuid import uuid4

RETRIEVAL_LIMIT = 10
MAX_SNIPPET_CHARS = 1000
MAX_CONTEXT_CHARS = 16000
MAX_UPLOAD_MB = 200
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

class RegisterModel(BaseModel):
    username: str
    password: str


class LoginModel(BaseModel):
    username: str
    password: str

app = FastAPI()

ingestion_semaphore = asyncio.Semaphore(2)
ingestion_jobs: dict[str, dict] = {}


def _search_user_chunks(query_text: str, owner_id: str):
    vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
    table = vector_db.open_table('articles_chunks')
    return table.search(query=query_text).where(f"owner_id = '{owner_id}'").limit(RETRIEVAL_LIMIT).to_list()


def _save_upload_file(src_file, dest_path: Path) -> None:
    with open(dest_path, 'wb') as buffer:
        shutil.copyfileobj(src_file, buffer)


def _dedupe_results(results: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen_chunk_ids: set[str] = set()
    seen_signatures: set[str] = set()

    for item in results:
        chunk_id = str(item.get('chunk_id', ''))
        if chunk_id and chunk_id in seen_chunk_ids:
            continue

        content = (item.get('content') or '').strip()
        signature = content[:300]
        if signature and signature in seen_signatures:
            continue

        if chunk_id:
            seen_chunk_ids.add(chunk_id)
        if signature:
            seen_signatures.add(signature)
        deduped.append(item)

    return deduped


def _build_context(results: list[dict]) -> str:
    blocks: list[str] = []
    total_chars = 0

    for item in results:
        snippet = (item.get('content') or '')[:MAX_SNIPPET_CHARS]
        block = (
            f"Document: {item.get('filename')}\n"
            f"Source Path: {item.get('filepath')}\n"
            f"Content Snippet:\n{snippet}"
        )

        block_len = len(block) + 2
        if total_chars + block_len > MAX_CONTEXT_CHARS:
            break

        blocks.append(block)
        total_chars += block_len

    return "\n\n".join(blocks)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"status": "ok", "message": "RAG API is running"}

@app.post('/rag/query')
async def query_documentation(query: Prompt, current_user: dict = Depends(get_current_user)):
    try:
        results = await asyncio.to_thread(_search_user_chunks, query.prompt, str(current_user['id']))
        results = _dedupe_results(results)

        if not results:
            raise HTTPException(status_code=404, detail="No documents found for this user")

        combined = _build_context(results)

        prompt_with_context = (
            "Use only the provided context. Copy names, titles, dates, and numbers exactly as written. "
            "If a requested fact is missing, say 'Not found in provided context.'\n\n"
            f"Context:\n{combined}\n\nQuestion: {query.prompt}"
        )
        result = await rag_agent.run(prompt_with_context)
        
        return {
            "answer": result.output,
            "filepath": ", ".join(list(set(r.get('filename') for r in results)))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/auth/register')
async def register_user(payload: RegisterModel):
    user = auth.create_user(payload.username, payload.password)
    return {"status": "success", "user": user}


@app.post('/auth/login')
async def login(payload: LoginModel):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"id": user['id'], "username": user['username']})
    return {"access_token": token}


def _set_job_status(job_id: str, status: str, error: str | None = None) -> None:
    job = ingestion_jobs.get(job_id)
    if not job:
        return
    job['status'] = status
    job['error'] = error


async def process_document_background(pdf_path: Path, owner_id: str, job_id: str):
    async with ingestion_semaphore:
        try:
            _set_job_status(job_id, 'processing')
            result = await asyncio.to_thread(ingest_single_document, pdf_path, owner_id)
            if result.get('success'):
                _set_job_status(job_id, 'completed')
            else:
                _set_job_status(job_id, 'failed', result.get('error') or result.get('message'))
        except Exception as e:
            _set_job_status(job_id, 'failed', str(e))
            print(f"Error processing {pdf_path.name}: {e}")

@app.post('/rag/upload')
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
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
    
    user_dir = DATA_PATH / current_user['username']
    user_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = user_dir / Path(file.filename).name
    
    try:
        await asyncio.to_thread(_save_upload_file, file.file, pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")
    finally:
        file.file.close()

    job_id = str(uuid4())
    ingestion_jobs[job_id] = {
        'owner_id': str(current_user['id']),
        'filename': file.filename,
        'status': 'queued',
        'error': None,
    }

    background_tasks.add_task(process_document_background, pdf_path, str(current_user['id']), job_id)
    
    return {
        "status": "success",
        "message": "File uploaded. Processing started.",
        "filename": file.filename,
        "job_id": job_id,
    }


@app.get('/rag/upload-status/{job_id}')
async def get_upload_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = ingestion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if str(job.get('owner_id')) != str(current_user['id']):
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        'job_id': job_id,
        'filename': job.get('filename'),
        'status': job.get('status'),
        'error': job.get('error'),
    }

@app.get('/rag/documents')
async def get_documents(current_user: dict = Depends(get_current_user)):
    return {"documents": list_documents(owner_id=str(current_user['id']))}

@app.delete('/rag/documents/{doc_id}')
async def remove_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    result = delete_document(doc_id, owner_id=str(current_user['id']))
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=500, detail=result['message'])

@app.post('/rag/reset')
async def reset_database(current_user: dict = Depends(get_current_user)):
    result = reset_knowledge_base(owner_id=str(current_user['id']))
    if result['success']:
        return result
    else:
        print(f"RESET ERROR: {result['message']}")
        raise HTTPException(status_code=500, detail=result['message'])