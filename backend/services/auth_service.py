from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.orm import Session
import secrets
import redis
from ..models.user import User
from ..config.database import get_db
import random  # Added for numeric OTP

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REDIS_URL = "redis://redis:6379"

r = redis.Redis.from_url(REDIS_URL)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "secret-key", algorithm=ALGORITHM)

def authenticate_user(db_user: User, password: str) -> Optional[str]:
    if not db_user or not verify_password(password, str(db_user.password_hash)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return create_access_token(data={"sub": db_user.username})

def generate_otp() -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(6))  # Numeric 6-digit OTP

def store_otp(email: str, otp: str, expiry=300):
    r.setex(f"otp:{email}", expiry, otp)

def verify_otp(email: str, otp: str) -> bool:
    stored: Optional[bytes] = r.get(f"otp:{email}")# type: ignore
    if stored is not None and stored.decode("utf-8") == otp:
        r.delete(f"otp:{email}")
        return True
    return False

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, "secret-key", algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return db_user.id # type: ignore