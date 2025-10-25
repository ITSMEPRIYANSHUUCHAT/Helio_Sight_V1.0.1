from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.customer import Customer, CustomerCreate, CustomerResponse
from ..config.database import get_db
from ..services.auth_service import get_current_user  # Now defined
from sqlalchemy.exc import IntegrityError
import uuid

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/create", response_model=CustomerResponse)
def create_customer(customer_data: CustomerCreate, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = str(uuid.uuid4())
    db_customer = Customer(
        customer_id=customer_id,
        user_id=current_user_id,
        customer_name=customer_data.customer_name,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address
    )
    db.add(db_customer)
    try:
        db.commit()
        db.refresh(db_customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer creation failed")
    return db_customer

@router.get("/", response_model=list[CustomerResponse])
def get_customers(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    customers = db.query(Customer).filter(Customer.user_id == current_user_id).all()
    return customers