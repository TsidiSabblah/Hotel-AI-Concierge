from sqlalchemy import Column, String, DateTime, JSON, Boolean, Float
from app.db import Base
import uuid
from datetime import datetime

class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # hotel, apartment, rental, coworking
    whatsapp_number = Column(String(20), unique=True, nullable=False)
    logo_url = Column(String(500))
    address = Column(String(500))
    city = Column(String(100))
    country = Column(String(100), default="Ghana")
    settings = Column(JSON, default={})  # custom config
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BusinessUser(Base):
    __tablename__ = "business_users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    role = Column(String(50), default="manager")  # owner, manager, staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BusinessKnowledge(Base):
    __tablename__ = "business_knowledge"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), nullable=False)
    category = Column(String(50))  # breakfast, wifi, pool, etc.
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)