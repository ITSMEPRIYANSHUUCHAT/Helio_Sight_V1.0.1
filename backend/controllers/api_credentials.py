from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.api_credential import ApiCredential, ApiCredentialCreate, ApiCredentialResponse
from ..config.database import get_db
from ..services.auth_service import get_current_user
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api-credentials", tags=["api-credentials"])

@router.post("/create", response_model=ApiCredentialResponse)
def create_api_credential(credential_data: ApiCredentialCreate, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate customer belongs to user
    customer = db.query(Customer).filter(Customer.customer_id == credential_data.customer_id, Customer.user_id == current_user_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found or unauthorized")
    
    db_credential = ApiCredential(
        user_id=current_user_id,
        customer_id=credential_data.customer_id,
        api_provider=credential_data.api_provider,
        username=credential_data.username,
        password=credential_data.password,
        api_key=credential_data.api_key,
        api_secret=credential_data.api_secret
    )
    db.add(db_credential)
    try:
        db.commit()
        db.refresh(db_credential)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credential creation failed")
    return db_credential

@router.get("/", response_model=list[ApiCredentialResponse])
def get_api_credentials(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    credentials = db.query(ApiCredential).filter(ApiCredential.user_id == current_user_id).all()
    return credentials