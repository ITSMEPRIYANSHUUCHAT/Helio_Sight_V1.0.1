from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .user import Base  # Shared Base

class Device(Base):
    __tablename__ = "devices"
    device_sn = Column(String, primary_key=True, index=True)  # Changed: device_sn as PK (matches schema)
    plant_id = Column(String, ForeignKey("plants.plant_id"), nullable=False)
    inverter_model = Column(String)
    panel_model = Column(String)
    pv_count = Column(Float)  # INTEGER in schema, but Float for flexibility
    string_count = Column(Float)
    first_install_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DeviceResponse(BaseModel):
    device_sn: str  # Changed: device_sn instead of id
    plant_id: str
    inverter_model: Optional[str]
    panel_model: Optional[str]
    pv_count: Optional[float]
    string_count: Optional[float]
    first_install_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True