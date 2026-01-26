import lancedb
from pathlib import Path
from pypdf import PdfReader
from backend.constants import VECTOR_DATABASE_PATH, DATA_PATH
from backend.data_models import Article


def extract_text_from_pdf(pdf_path: Path) -> str:

    reader = PdfReader(pdf_path)
    all_text = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text += text + '\n'
    return all_text


def save_text_to_file(text: str, output_path: Path) -> None:

    with open(output_path, 'w', encoding="utf-8") as file:
        file.write(text)


def ingest_single_document(pdf_path: Path, table) -> dict:

    try:

        content = extract_text_from_pdf(pdf_path)
        

        txt_filename = f"{pdf_path.stem}.txt"
        txt_path = DATA_PATH / txt_filename
        save_text_to_file(content, txt_path)

        doc_id = pdf_path.stem
        

        table.delete(f"doc_id = '{doc_id}'")
        table.compact_files()
        

        table.add([
            {
                "doc_id": doc_id,
                "filepath": str(txt_path),
                "filename": pdf_path.stem,
                "content": content
            }
        ])
        
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
        table = vector_db.open_table("articles")
    except:
        table = vector_db.create_table("articles", schema=Article, mode="overwrite")
    
    return table


def list_all_documents() -> list:

    try:
        table = get_vector_db_table()
        docs = table.to_pandas()[['doc_id', 'filename']].drop_duplicates().to_dict('records')
        return docs
    except Exception as e:
        return []


def delete_document(doc_id: str) -> dict:

    try:
        table = get_vector_db_table()
        table.delete(f"doc_id = '{doc_id}'")
        table.compact_files()
        
        txt_path = DATA_PATH / f"{doc_id}.txt"
        if txt_path.exists():
            txt_path.unlink()
        
        pdf_path = DATA_PATH / f"{doc_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
        
        return {
            "success": True,
            "message": f"Successfully deleted document: {doc_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete document: {str(e)}"
        }


def reset_knowledge_base() -> dict:

    try:
        import shutil
        
        if VECTOR_DATABASE_PATH.exists():
            shutil.rmtree(VECTOR_DATABASE_PATH)
        
        VECTOR_DATABASE_PATH.mkdir(parents=True, exist_ok=True)
        
        vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
        vector_db.create_table("articles", schema=Article, mode="overwrite")
        
        for txt_file in DATA_PATH.glob("*.txt"):
            txt_file.unlink()
        for pdf_file in DATA_PATH.glob("*.pdf"):
            pdf_file.unlink()
        
        return {
            "success": True,
            "message": "Knowledge base has been completely reset"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reset knowledge base: {str(e)}"
        }