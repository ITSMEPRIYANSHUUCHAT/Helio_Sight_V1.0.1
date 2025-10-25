from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from ..models.user import User, Login, UserCreate, Token, UserResponse
from ..services.auth_service import authenticate_user, get_password_hash, generate_otp, store_otp, verify_otp, get_current_user, create_access_token
from ..config.database import get_db
import uuid
from datetime import datetime
import random  # Added for numeric OTP
from pydantic import BaseModel
from os import getenv
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from ..services.auth_service import r  # Add this to import Redis client
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = getenv("JWT_SECRET_KEY", "secret-key")  # Default for dev
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
OTP_EXPIRY_SECONDS = int(getenv("OTP_EXPIRY_SECONDS", 300))
ALGORITHM = "HS256"
class OTPData(BaseModel):  # New model for body
    email: str
    otp: str
router = APIRouter(prefix="/auth", tags=["auth"])

# Update generate_otp in this file or auth_service.py
def generate_otp() -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(6))  # Numeric 6-digit OTP

@router.post("/login")
def login(login_data: Login, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == login_data.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = authenticate_user(db_user, login_data.password)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Safe commit for last_login
    try:
        db_user.last_login = datetime.utcnow()  # type: ignore        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Login commit error (non-fatal): {e}")
    
    return {
        "token": access_token,
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "fullname": db_user.name,
            "email": db_user.email,
            "userType": db_user.usertype,
        }
    }

@router.post("/register", response_model=dict)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email exists")
    
    hashed_pw = get_password_hash(user_data.password)
    db_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_pw,
        usertype=user_data.usertype
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")
    
    otp = generate_otp()
    store_otp(user_data.email, otp)
    return {"message": "User created. Check email for OTP.", "user_id": db_user.id}

@router.post("/verify-otp", response_model=dict)
def verify_otp_endpoint(otp_data: OTPData, db: Session = Depends(get_db)):  # Use model for body
    print(f"Received OTP data: {otp_data}")  # Debug (now typed)
    email = otp_data.email
    otp = otp_data.otp
    if not email or not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and OTP required")
    
    if not verify_otp(email, otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user.verified = True  # type: ignore[assignment]
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Verify OTP commit error: {e}")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {
        "token": access_token,
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "fullname": db_user.name,
            "email": db_user.email,
            "userType": db_user.usertype,
        }
    }

@router.get("/me", response_model=UserResponse)
def me(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, "secret-key", algorithms=[ALGORITHM])
    jti = payload.get("jti")
    if jti:
        r.setex(f"blacklist:{jti}", ACCESS_TOKEN_EXPIRE_MINUTES * 60, "true")  # Blacklist with expiry
    return {"message": "Logged out successfully"}