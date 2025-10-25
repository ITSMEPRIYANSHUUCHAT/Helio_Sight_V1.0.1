# Update backend/controllers/dashboard.py (Add Timeseries Endpoint)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.plant import Plant, PlantResponse
from ..models.device import Device, DeviceResponse
from ..models.device_data import DeviceDataHistorical, DeviceDataResponse  # Add import
from ..models.user import Customer
from ..config.database import get_db
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/plants", response_model=List[PlantResponse])
def get_plants(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    plants = db.query(Plant).join(Customer, Plant.customer_id == Customer.customer_id).filter(Customer.user_id == current_user_id).all()
    if not plants:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No plants found for user")
    return plants

@router.get("/devices", response_model=List[DeviceResponse])
def get_devices(plant_id: Optional[str] = None, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Device).join(Plant, Device.plant_id == Plant.plant_id).join(Customer, Plant.customer_id == Customer.customer_id).filter(Customer.user_id == current_user_id)
    if plant_id:
        query = query.filter(Plant.plant_id == plant_id)
    devices = query.all()
    if not devices:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No devices found for user")
    return devices

@router.get("/timeseries/{device_sn}", response_model=List[DeviceDataResponse])
def get_timeseries(
    device_sn: str,
    metric: Optional[str] = Query(None, description="Metric to filter (e.g., total_power)"),
    timeRange: Optional[str] = Query("24h", description="Time range (24h, 7d)"),
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate timeRange
    if timeRange == "24h":
        start = datetime.utcnow() - timedelta(hours=24)
    elif timeRange == "7d":
        start = datetime.utcnow() - timedelta(days=7)
    else:
        raise HTTPException(status_code=400, detail="Invalid timeRange (use 24h or 7d)")
    
    # Query with filter
    query = db.query(DeviceDataHistorical).filter(
        DeviceDataHistorical.device_sn == device_sn,
        DeviceDataHistorical.timestamp >= start
    ).order_by(DeviceDataHistorical.timestamp.desc()).limit(1000)  # Limit for performance
    
    data = query.all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for device")
    
    # Filter metric if specified
    if metric:
        filtered = [
            {"timestamp": item.timestamp, metric: getattr(item, metric, None)} 
            for item in data
        ]
        return filtered
    else:
        # Full data
        return [item.__dict__ for item in data]