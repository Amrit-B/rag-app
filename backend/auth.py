from datetime import datetime, timedelta, timezone
from passlib.hash import pbkdf2_sha256
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError

from backend.constants import SECRET_KEY
from backend.database import SessionLocal, User

security = HTTPBearer()


def create_user(username: str, password: str, is_admin: bool = False) -> dict:
    clean_username = username.strip()
    if len(clean_username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

    db = SessionLocal()
    hashed = pbkdf2_sha256.hash(password)
    db_user = User(username=clean_username, password_hash=hashed, is_admin=is_admin)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"id": db_user.id, "username": db_user.username, "is_admin": bool(db_user.is_admin)}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username.strip()).first()
        if not user:
            return None
        if pbkdf2_sha256.verify(password, user.password_hash):
            return {"id": user.id, "username": user.username, "is_admin": bool(user.is_admin)}
        return None
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: int = 60 * 24) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return token


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id")
        username = payload.get("username")
        is_admin = bool(payload.get("is_admin", False))
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"id": user_id, "username": username, "is_admin": is_admin}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
