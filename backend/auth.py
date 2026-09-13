from datetime import datetime, timedelta
# pyrefly: ignore [missing-module-attribute]
from passlib.hash import pbkdf2_sha256
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError

from backend.constants import SECRET_KEY
from backend.database import SessionLocal, User, init_db

security = HTTPBearer()


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
