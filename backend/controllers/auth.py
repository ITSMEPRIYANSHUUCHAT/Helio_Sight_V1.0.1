from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.user import User, Login, Token  # Relative from controllers
from ..services.auth_service import authenticate_user  # Relative
from ..config.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(login_data: Login, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == login_data.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = authenticate_user(db_user, login_data.password)
    if not access_token:  # Explicit check
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=access_token, token_type="bearer")