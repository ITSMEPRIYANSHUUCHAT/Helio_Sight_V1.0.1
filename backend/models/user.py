from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

Base = declarative_base()  # Shared

class UserType(str, Enum):
    CUSTOMER = "customer"
    INSTALLER = "installer"

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    usertype = Column(String, nullable=False)
    profile = Column(JSON, default=dict)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    customer_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))

# Pydantic
class Login(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    name: str
    email: EmailStr
    password: str
    usertype: UserType

class UserResponse(BaseModel):
    id: str
    username: str
    name: str
    email: str
    usertype: UserType
    verified: bool
    profile: dict

    class Config:
        from_attributes = True

class CustomerCreate(BaseModel):
    customer_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    customer_id: str
    customer_name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"