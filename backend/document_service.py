from datetime import timedelta
from pathlib import Path
import os
import lancedb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.constants import VECTOR_DATABASE_PATH, DATA_PATH
from backend.data_models import ChunkArticle, embedding_model
from backend.preprocessor import clean_text
from backend.database import (
    db_save_document,
    db_list_documents,
    db_get_document,
    db_delete_document,
    db_reset_documents,
)


def extract_and_clean_pdf(pdf_path: Path) -> str:
    """Extracts text from each PDF page and applies noise-cleaning preprocessor."""
    reader = PdfReader(pdf_path)
    page_texts: list[str] = []
    for page in reader.pages:
        raw = page.extract_text()
        if raw:
            cleaned_page = clean_text(raw)
            if cleaned_page:
                page_texts.append(cleaned_page)
    return "\n\n".join(page_texts)


def get_technical_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
    """
    Returns a RecursiveCharacterTextSplitter optimized for technical documents,
    preserving code fences, markdown headers, and structured lists.
    """
    return RecursiveCharacterTextSplitter(
        separators=[
            "\n\n```",
            "\n```",
            "\n\n## ",
            "\n\n# ",
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )


def _safe_delete_path(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


def _compute_embeddings(text_chunks: list[str], batch_size: int = 16) -> list:
    if not text_chunks:
        return []

    embeddings: list = []
    total = len(text_chunks)
    for i in range(0, total, batch_size):
        batch = text_chunks[i : i + batch_size]
        batch_embeddings = embedding_model.compute_source_embeddings(batch)
        embeddings.extend(batch_embeddings)

    if len(embeddings) != len(text_chunks):
        raise ValueError(f"Embedding count ({len(embeddings)}) does not match chunk count ({len(text_chunks)})")

    return embeddings


def get_vector_db_table():
    VECTOR_DATABASE_PATH.mkdir(parents=True, exist_ok=True)
    vector_db = lancedb.connect(uri=VECTOR_DATABASE_PATH)
    try:
        table = vector_db.open_table("articles_chunks")
    except Exception:
        table = vector_db.create_table("articles_chunks", schema=ChunkArticle, mode="overwrite")
    return table


def ingest_single_document(pdf_path: Path, owner_id: str) -> dict:
    """
    Ingests a PDF:
    1. Extracts and cleans text
    2. Generates technical chunks using RecursiveCharacterTextSplitter
    3. Computes embeddings
    4. Upserts into LanceDB table
    5. Saves metadata into SQLite
    """
    doc_id = pdf_path.stem
    file_size = os.path.getsize(pdf_path) if pdf_path.exists() else 0

    try:
        table = get_vector_db_table()
        cleaned_content = extract_and_clean_pdf(pdf_path)

        if not cleaned_content.strip():
            raise ValueError(f"No extractable text found in {pdf_path.name}. Ensure it is not a scanned or image-only PDF.")

        txt_path = pdf_path.with_suffix(".txt")
        txt_path.write_text(cleaned_content, encoding="utf-8")

        # Split using technical recursive splitter
        splitter = get_technical_text_splitter()
        text_chunks = splitter.split_text(cleaned_content)

        if not text_chunks:
            raise ValueError("Text splitting resulted in 0 chunks.")

        # Compute embeddings in batches
        embeddings = _compute_embeddings(text_chunks)

        # Delete any previous chunks for this document and owner
        try:
            table.delete(f"doc_id = '{doc_id}' AND owner_id = '{owner_id}'")
        except Exception:
            pass

        # Build chunk records
        chunk_records = []
        for i, chunk in enumerate(text_chunks):
            chunk_records.append({
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{i}",
                "filepath": str(txt_path),
                "filename": pdf_path.name,
                "content": chunk,
                "owner_id": owner_id,
                "embedding": embeddings[i],
            })

        table.add(chunk_records)

        # Record in SQLite relational metadata
        meta = db_save_document(
            doc_id=doc_id,
            owner_id=owner_id,
            filename=pdf_path.name,
            filepath=str(pdf_path),
            file_size_bytes=file_size,
            chunk_count=len(chunk_records),
            status="completed",
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "filename": pdf_path.name,
            "chunk_count": len(chunk_records),
            "file_size_bytes": file_size,
            "message": f"Successfully processed and ingested {pdf_path.name} ({len(chunk_records)} chunks)",
        }

    except Exception as e:
        db_save_document(
            doc_id=doc_id,
            owner_id=owner_id,
            filename=pdf_path.name,
            filepath=str(pdf_path),
            file_size_bytes=file_size,
            chunk_count=0,
            status="failed",
            error_message=str(e),
        )
        return {
            "success": False,
            "filename": pdf_path.name,
            "error": str(e),
            "message": f"Failed to process {pdf_path.name}: {str(e)}",
        }


def list_documents(owner_id: str) -> list[dict]:
    """Queries relational SQLite metadata directly (sub-millisecond, no to_pandas())."""
    return db_list_documents(owner_id=owner_id)


def delete_document(doc_id: str, owner_id: str) -> dict:
    """Deletes document from LanceDB, filesystem, and SQLite."""
    try:
        # Delete from LanceDB
        table = get_vector_db_table()
        try:
            table.delete(f"doc_id = '{doc_id}' AND owner_id = '{owner_id}'")
        except Exception:
            pass

        # Lookup and delete files
        doc = db_get_document(doc_id=doc_id, owner_id=owner_id)
        if doc and doc.get("filepath"):
            pdf_path = Path(doc["filepath"])
            _safe_delete_path(pdf_path)
            _safe_delete_path(pdf_path.with_suffix(".txt"))

        # Delete from SQLite
        db_delete_document(doc_id=doc_id, owner_id=owner_id)

        return {
            "success": True,
            "message": f"Successfully deleted document: {doc_id}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete document: {str(e)}",
        }


def reset_knowledge_base(owner_id: str) -> dict:
    """Deletes all documents and vector chunks for a specific owner."""
    try:
        table = get_vector_db_table()
        try:
            table.delete(f"owner_id = '{owner_id}'")
            table.compact_files()
            table.cleanup_old_versions(older_than=timedelta(seconds=0))
        except Exception:
            pass

        # Cleanup files on disk
        deleted_paths = db_reset_documents(owner_id=owner_id)
        for fp in deleted_paths:
            p = Path(fp)
            _safe_delete_path(p)
            _safe_delete_path(p.with_suffix(".txt"))

        return {
            "success": True,
            "message": "Knowledge base has been completely reset",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reset knowledge base: {str(e)}",
        }