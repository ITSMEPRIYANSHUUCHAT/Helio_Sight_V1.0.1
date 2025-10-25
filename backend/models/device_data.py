from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .user import Base  # Shared Base

class DeviceDataHistorical(Base):
    __tablename__ = "device_data_historical"
    device_sn = Column(String, ForeignKey("devices.device_sn"), primary_key=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True)  # Fixed: DateTime(timezone=True)
    
    # PV Voltages & Currents (pv01 to pv12)
    pv01_voltage = Column(Float)
    pv01_current = Column(Float)
    pv02_voltage = Column(Float)
    pv02_current = Column(Float)
    pv03_voltage = Column(Float)
    pv03_current = Column(Float)
    pv04_voltage = Column(Float)
    pv04_current = Column(Float)
    pv05_voltage = Column(Float)
    pv05_current = Column(Float)
    pv06_voltage = Column(Float)
    pv06_current = Column(Float)
    pv07_voltage = Column(Float)
    pv07_current = Column(Float)
    pv08_voltage = Column(Float)
    pv08_current = Column(Float)
    pv09_voltage = Column(Float)
    pv09_current = Column(Float)
    pv10_voltage = Column(Float)
    pv10_current = Column(Float)
    pv11_voltage = Column(Float)
    pv11_current = Column(Float)
    pv12_voltage = Column(Float)
    pv12_current = Column(Float)
    
    # AC Voltages & Currents
    r_voltage = Column(Float)
    s_voltage = Column(Float)
    t_voltage = Column(Float)
    r_current = Column(Float)
    s_current = Column(Float)
    t_current = Column(Float)
    rs_voltage = Column(Float)
    st_voltage = Column(Float)
    tr_voltage = Column(Float)
    frequency = Column(Float)
    
    # Power & Energy
    total_power = Column(Float)
    reactive_power = Column(Float)
    energy_today = Column(Float)
    cuf = Column(Float)
    pr = Column(Float)
    state = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DeviceDataResponse(BaseModel):
    device_sn: str
    timestamp: datetime
    # PV Voltages & Currents
    pv01_voltage: Optional[float]
    pv01_current: Optional[float]
    pv02_voltage: Optional[float]
    pv02_current: Optional[float]
    pv03_voltage: Optional[float]
    pv03_current: Optional[float]
    pv04_voltage: Optional[float]
    pv04_current: Optional[float]
    pv05_voltage: Optional[float]
    pv05_current: Optional[float]
    pv06_voltage: Optional[float]
    pv06_current: Optional[float]
    pv07_voltage: Optional[float]
    pv07_current: Optional[float]
    pv08_voltage: Optional[float]
    pv08_current: Optional[float]
    pv09_voltage: Optional[float]
    pv09_current: Optional[float]
    pv10_voltage: Optional[float]
    pv10_current: Optional[float]
    pv11_voltage: Optional[float]
    pv11_current: Optional[float]
    pv12_voltage: Optional[float]
    pv12_current: Optional[float]
    
    # AC Voltages & Currents
    r_voltage: Optional[float]
    s_voltage: Optional[float]
    t_voltage: Optional[float]
    r_current: Optional[float]
    s_current: Optional[float]
    t_current: Optional[float]
    rs_voltage: Optional[float]
    st_voltage: Optional[float]
    tr_voltage: Optional[float]
    frequency: Optional[float]
    
    # Power & Energy
    total_power: Optional[float]
    reactive_power: Optional[float]
    energy_today: Optional[float]
    cuf: Optional[float]
    pr: Optional[float]
    state: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True