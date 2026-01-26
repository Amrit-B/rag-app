from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.rag import rag_agent
from backend.data_models import Prompt
from backend.document_service import ingest_single_document, get_vector_db_table, list_all_documents, delete_document, reset_knowledge_base
from backend.constants import DATA_PATH
from pathlib import Path
import shutil

app = FastAPI()

@app.post('/rag/query')
async def query_documentation(query: Prompt):
    result = await rag_agent.run(query.prompt)

    return result.output

@app.post('/rag/upload')
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    pdf_path = DATA_PATH / file.filename
    
    try:
        with open(pdf_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        table = get_vector_db_table()
        result = ingest_single_document(pdf_path, table)
        
        if result['success']:
            return {
                "status": "success",
                "message": result['message'],
                "filename": result['filename']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        file.file.close()

@app.get('/rag/documents')
async def get_documents():
    docs = list_all_documents()
    return {"documents": docs}

@app.delete('/rag/documents/{doc_id}')
async def remove_document(doc_id: str):
    result = delete_document(doc_id)
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=500, detail=result['message'])

@app.post('/rag/reset')
async def reset_database():
    result = reset_knowledge_base()
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=500, detail=result['message'])