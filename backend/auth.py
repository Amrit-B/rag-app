import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from pathlib import Path
from passlib.hash import pbkdf2_sha256
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.constants import DATA_PATH, SECRET_KEY, AUTH_DB_PATH


# SQLAlchemy Setup
SQLALCHEMY_DATABASE_URL = f"sqlite:///{AUTH_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

security = HTTPBearer()


def init_db():
    AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def create_user(username: str, password: str) -> dict:
    db = SessionLocal()
    hashed = pbkdf2_sha256.hash(password)
    db_user = User(username=username, password_hash=hashed)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"id": db_user.id, "username": db_user.username}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if pbkdf2_sha256.verify(password, user.password_hash):
            return {"id": user.id, "username": user.username}
        return None
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: int = 60 * 24) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return token


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id")
        username = payload.get("username")
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"id": user_id, "username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
