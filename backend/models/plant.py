from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime  # Added this import
from .user import Base  # Shared Base (assuming user.py has Base)
from typing import Optional  #
class Plant(Base):
    __tablename__ = "plants"
    plant_id = Column(String, primary_key=True, index=True)  # Matches SQL: TEXT PRIMARY KEY
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False)  # FK to customers
    plant_name = Column(String, nullable=False)
    capacity = Column(Float, nullable=False)  # DOUBLE PRECISION CHECK (capacity >= 0)
    total_energy = Column(Float, nullable=True)  # DOUBLE PRECISION CHECK (total_energy >= 0)
    install_date = Column(DateTime)  # DATE
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic Schemas
class PlantCreate(BaseModel):
    plant_id: str
    customer_id: str
    plant_name: str
    capacity: float
    total_energy: Optional[float] = None
    install_date: Optional[datetime] = None  # Now datetime is imported
    location: Optional[str] = None

class PlantResponse(BaseModel):
    plant_id: str
    customer_id: str
    plant_name: str
    capacity: float
    total_energy: Optional[float] = None
    install_date: Optional[datetime]
    location: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True