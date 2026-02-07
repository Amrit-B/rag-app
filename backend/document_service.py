import lancedb
from datetime import timedelta
from pathlib import Path
from pypdf import PdfReader
from backend.constants import VECTOR_DATABASE_PATH, DATA_PATH
from backend.data_models import ChunkArticle


def extract_text_from_pdf(pdf_path: Path) -> str:

    reader = PdfReader(pdf_path)
    all_text = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text += text + '\n'
    return all_text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if not text:
        return []
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(text), step):
        chunks.append(text[i : i + chunk_size])
    return chunks


def ingest_single_document(pdf_path: Path, owner_id: str, progress_callback=None) -> dict:

    try:
        if progress_callback: progress_callback(0.1, "Extracting text...")
        table = get_vector_db_table()
        content = extract_text_from_pdf(pdf_path)
        

        txt_path = pdf_path.with_suffix('.txt')
        txt_path.write_text(content, encoding="utf-8")

        doc_id = pdf_path.stem
        

        table.delete(f"doc_id = '{doc_id}' AND owner_id = '{owner_id}'")
            
        table.compact_files()
        
        if progress_callback: progress_callback(0.2, "Chunking text...")
        text_chunks = chunk_text(content)
        
        embeddings = []
        if text_chunks:
            from backend.data_models import embedding_model
            
            total = len(text_chunks)
            batch_size = 10
            for i in range(0, total, batch_size):
                if progress_callback:
                    p = 0.2 + (0.7 * (i / total))
                    progress_callback(p, f"Embedding chunks {i}/{total}...")
                
                batch = text_chunks[i : i + batch_size]
                batch_embeddings = embedding_model.compute_source_embeddings(batch)
                embeddings.extend(batch_embeddings)
            
        chunk_records = []
        for i, chunk in enumerate(text_chunks):
            chunk_records.append({
                'doc_id': doc_id,
                'chunk_id': f"{doc_id}_chunk_{i}",
                'filepath': str(txt_path),
                'filename': pdf_path.stem,
                'content': chunk,
                'owner_id': owner_id,
                'embedding': embeddings[i]
            })

        if progress_callback: progress_callback(0.95, "Saving to database...")
        if chunk_records:
            table.add(chunk_records)
        
        if progress_callback: progress_callback(1.0, "Processing complete")
        return {
            "success": True,
            "doc_id": doc_id,
            "filename": pdf_path.name,
            "message": f"Successfully processed and ingested {pdf_path.name}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "filename": pdf_path.name,
            "error": str(e),
            "message": f"Failed to process {pdf_path.name}: {str(e)}"
        }


def get_vector_db_table():
    vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
    
    try:
        table = vector_db.open_table("articles_chunks")
    except Exception:
        table = vector_db.create_table("articles_chunks", schema=ChunkArticle, mode="overwrite")
    
    return table


def list_documents(owner_id: str) -> list:

    try:
        table = get_vector_db_table()
        df = table.to_pandas()
        # Filter by owner_id before returning
        df = df[df['owner_id'] == owner_id]
        docs = df[['doc_id', 'filename', 'owner_id']].drop_duplicates().to_dict('records')
        return docs
    except Exception as e:
        return []


def delete_document(doc_id: str, owner_id: str) -> dict:

    try:
        table = get_vector_db_table()
        
        # Get filepaths before deletion
        try:
            df = table.to_pandas()
            matches = df[(df['doc_id'] == doc_id) & (df['owner_id'] == owner_id)]
            if not matches.empty:
                txt_path = Path(matches.iloc[0]['filepath'])
                txt_path.unlink(missing_ok=True)
                txt_path.with_suffix('.pdf').unlink(missing_ok=True)
        except Exception:
            pass

        table.delete(f"doc_id = '{doc_id}' AND owner_id = '{owner_id}'")
        table.compact_files()
        
        
        return {
            "success": True,
            "message": f"Successfully deleted document: {doc_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete document: {str(e)}"
        }


def reset_knowledge_base(owner_id: str) -> dict:

    try:
        table = get_vector_db_table()
        df = table.to_pandas()
        user_files = set(df.loc[df['owner_id'] == owner_id, 'filepath'])
            
        for fp in user_files:
            txt_path = Path(fp)
            txt_path.unlink(missing_ok=True)
            txt_path.with_suffix('.pdf').unlink(missing_ok=True)
            
            user_dir = txt_path.parent
            if user_dir != DATA_PATH and user_dir.exists() and not any(user_dir.iterdir()):
                user_dir.rmdir()

        table.delete(f"owner_id = '{owner_id}'")
        table.compact_files()
        table.cleanup_old_versions(older_than=timedelta(seconds=0))

        return {
            "success": True,
            "message": "Knowledge base has been completely reset"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reset knowledge base: {str(e)}"
        }