from datetime import datetime, timezone
from pathlib import Path
import json
import os
from uuid import uuid4

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.constants import AUTH_DB_PATH

SQLALCHEMY_DATABASE_URL = f"sqlite:///{AUTH_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("DocumentRecord", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="completed")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user_rel_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources_json = Column(Text, default="[]")  # JSON string of sources
    route_taken = Column(String, nullable=True)  # 'vectorstore', 'websearch', 'hybrid'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")


def init_db():
    AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    # Automatic SQLite migration: ensure is_admin column exists
    with engine.connect() as conn:
        try:
            from sqlalchemy import text
            cursor = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in cursor.fetchall()]
            if "is_admin" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                conn.commit()
        except Exception as e:
            print(f"Migration notice: {e}")

    # Seed admin user if configured via environment variables
    admin_user_name = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if admin_user_name and admin_pass:
        db = SessionLocal()
        try:
            from passlib.hash import pbkdf2_sha256
            existing = db.query(User).filter(User.username == admin_user_name.strip()).first()
            if existing:
                existing.is_admin = True
            else:
                hashed = pbkdf2_sha256.hash(admin_pass)
                new_admin = User(username=admin_user_name.strip(), password_hash=hashed, is_admin=True)
                db.add(new_admin)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Warning seeding admin user: {e}")
        finally:
            db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Document Metadata CRUD
def db_save_document(
    doc_id: str,
    owner_id: str,
    filename: str,
    filepath: str,
    file_size_bytes: int = 0,
    chunk_count: int = 0,
    status: str = "completed",
    error_message: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(owner_id)).first() if owner_id.isdigit() else None
        doc = db.query(DocumentRecord).filter(DocumentRecord.doc_id == doc_id, DocumentRecord.owner_id == owner_id).first()
        if not doc:
            doc = DocumentRecord(
                doc_id=doc_id,
                owner_id=owner_id,
                filename=filename,
                filepath=filepath,
                file_size_bytes=file_size_bytes,
                chunk_count=chunk_count,
                status=status,
                error_message=error_message,
                user_id=user.id if user else None,
            )
            db.add(doc)
        else:
            # pyrefly: ignore [bad-assignment]
            doc.filename = filename
            # pyrefly: ignore [bad-assignment]
            doc.filepath = filepath
            # pyrefly: ignore [bad-assignment]
            doc.file_size_bytes = file_size_bytes
            # pyrefly: ignore [bad-assignment]
            doc.chunk_count = chunk_count
            # pyrefly: ignore [bad-assignment]
            doc.status = status
            # pyrefly: ignore [bad-assignment]
            doc.error_message = error_message
        db.commit()
        db.refresh(doc)
        return {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "file_size_bytes": doc.file_size_bytes,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
    finally:
        db.close()


def db_list_documents(owner_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        docs = db.query(DocumentRecord).filter(DocumentRecord.owner_id == owner_id).order_by(DocumentRecord.created_at.desc()).all()
        return [
            {
                "doc_id": d.doc_id,
                "filename": d.filename,
                "filepath": d.filepath,
                "file_size_bytes": d.file_size_bytes,
                "chunk_count": d.chunk_count,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    finally:
        db.close()


def db_get_document(doc_id: str, owner_id: str) -> dict | None:
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.doc_id == doc_id, DocumentRecord.owner_id == owner_id).first()
        if not doc:
            return None
        return {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "file_size_bytes": doc.file_size_bytes,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
    finally:
        db.close()


def db_delete_document(doc_id: str, owner_id: str) -> bool:
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.doc_id == doc_id, DocumentRecord.owner_id == owner_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False
    finally:
        db.close()


def db_reset_documents(owner_id: str) -> list[str]:
    """Deletes all document records for owner and returns their filepaths for filesystem cleanup."""
    db = SessionLocal()
    try:
        docs = db.query(DocumentRecord).filter(DocumentRecord.owner_id == owner_id).all()
        filepaths = [d.filepath for d in docs]
        for d in docs:
            db.delete(d)
        db.commit()
        # pyrefly: ignore [bad-return]
        return filepaths
    finally:
        db.close()


# Chat Session & History CRUD
def db_create_chat_session(user_id: str, title: str = "New Conversation") -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first() if user_id.isdigit() else None
        session = ChatSession(
            user_id=user_id,
            title=title,
            user_rel_id=user.id if user else None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {
            "id": session.id,
            "user_id": session.user_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    finally:
        db.close()


def db_list_chat_sessions(user_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ]
    finally:
        db.close()


def db_get_chat_session(session_id: str, user_id: str) -> dict | None:
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not session:
            return None
        return {
            "id": session.id,
            "user_id": session.user_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    finally:
        db.close()


def db_delete_chat_session(session_id: str, user_id: str) -> bool:
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    finally:
        db.close()


def db_add_chat_message(
    session_id: str,
    sender: str,
    content: str,
    sources: list[dict] | None = None,
    route_taken: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError(f"ChatSession {session_id} not found")

        sources_json = json.dumps(sources or [])
        msg = ChatMessage(
            session_id=session_id,
            sender=sender,
            content=content,
            sources_json=sources_json,
            route_taken=route_taken,
        )
        db.add(msg)
        # pyrefly: ignore [bad-assignment]
        session.updated_at = datetime.now(timezone.utc)

        # If it's the first user message, update title from content
        if sender == "user" and session.title == "New Conversation":
            clean_title = content.strip().split("\n")[0][:45]
            if clean_title:
                # pyrefly: ignore [bad-assignment]
                session.title = clean_title

        db.commit()
        db.refresh(msg)
        return {
            "id": msg.id,
            "session_id": msg.session_id,
            "sender": msg.sender,
            "content": msg.content,
            # pyrefly: ignore [bad-argument-type]
            "sources": json.loads(msg.sources_json or "[]"),
            "route_taken": msg.route_taken,
            "created_at": msg.created_at.isoformat(),
        }
    finally:
        db.close()


def db_get_chat_messages(session_id: str, user_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not session:
            return []
        msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [
            {
                "id": m.id,
                "session_id": m.session_id,
                "sender": m.sender,
                "content": m.content,
                # pyrefly: ignore [bad-argument-type]
                "sources": json.loads(m.sources_json or "[]"),
                "route_taken": m.route_taken,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ]
    finally:
        db.close()
