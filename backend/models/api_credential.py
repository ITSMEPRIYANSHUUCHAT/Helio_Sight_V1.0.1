from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
from enum import Enum as PyEnum

Base = declarative_base()

class ApiProvider(str, PyEnum):
    SHINEMONITOR = "shinemonitor"
    SOLARMAN = "solarman"
    SOLISCLOUD = "soliscloud"

class ApiCredential(Base):
    __tablename__ = "api_credentials"
    credential_id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False)
    api_provider = Column(Enum(ApiProvider), nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    api_key = Column(String)
    api_secret = Column(String)
    last_fetched = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))

class ApiCredentialCreate(BaseModel):
    customer_id: str
    api_provider: ApiProvider
    username: str
    password: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class ApiCredentialResponse(BaseModel):
    credential_id: int
    user_id: str
    customer_id: str
    api_provider: ApiProvider
    username: str
    last_fetched: Optional[str] = None

    class Config:
        from_attributes = True