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

class RegisterModel(BaseModel):
    username: str
    password: str


class LoginModel(BaseModel):
    username: str
    password: str

app = FastAPI()

processing_lock = asyncio.Lock()

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
    async with processing_lock:
        try:
            vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
            table = vector_db.open_table('articles_chunks')

            results = table.search(query=query.prompt).where(f"owner_id = '{current_user['id']}'").limit(50).to_list()

            if not results:
                raise HTTPException(status_code=404, detail="No documents found for this user")

            combined = "\n\n".join([
                f"Document: {r.get('filename')}\nSource Path: {r.get('filepath')}\nContent Snippet:\n{ (r.get('content') or '')[:4000] }"
                for r in results
            ])

            prompt_with_context = (
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


async def process_document_background(pdf_path: Path, owner_id: str):
    async with processing_lock:
        try:
            await asyncio.to_thread(ingest_single_document, pdf_path, owner_id)
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")

@app.post('/rag/upload')
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    user_dir = DATA_PATH / current_user['username']
    user_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = user_dir / Path(file.filename).name
    
    try:
        with open(pdf_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")
    finally:
        file.file.close()

    background_tasks.add_task(process_document_background, pdf_path, str(current_user['id']))
    
    return {
        "status": "success",
        "message": "File uploaded. Processing started.",
        "filename": file.filename
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