from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from datetime import datetime
import uuid
from app.config import settings

# Create engine for SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# ============== MODELS ==============

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Guest(Base):
    __tablename__ = "guests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(String(36))
    business_id = Column(String(36))  # ← ADD THIS LINE
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    room_number = Column(String(10))
    is_checked_in = Column(Boolean, default=False)
    check_in_date = Column(DateTime)
    check_out_date = Column(DateTime)
    total_spent = Column(Float, default=0.0)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(String(36))
    business_id = Column(String(36))  # ← ADD THIS LINE
    guest_id = Column(String(36))
    channel = Column(String(20))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    message_count = Column(Integer, default=0)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36))
    business_id = Column(String(36))  # ← ADD THIS LINE
    direction = Column(String(10))
    content = Column(Text, nullable=False)
    intent = Column(String(50))
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class HotelKnowledge(Base):
    __tablename__ = "hotel_knowledge"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(String(36))
    category = Column(String(50))
    question = Column(Text)
    answer = Column(Text)
    extra_data = Column(JSON)  # Changed from 'metadata' to 'extra_data'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    whatsapp_number = Column(String(20), unique=True)
    logo_url = Column(String(500))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100), default="Ghana")
    settings = Column(JSON, default={})
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
    role = Column(String(50), default="manager")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BusinessKnowledge(Base):
    __tablename__ = "business_knowledge"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), nullable=False)
    category = Column(String(50))
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============== DATABASE FUNCTIONS ==============

async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized (SQLite)")

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session

async def create_hotel(data: dict):
    async with AsyncSessionLocal() as session:
        hotel = Hotel(**data)
        session.add(hotel)
        await session.commit()
        await session.refresh(hotel)
        return hotel

async def get_hotel_by_phone(phone_number: str):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Hotel).where(Hotel.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

async def get_or_create_guest(phone_number: str, hotel_id: str):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Guest).where(
                Guest.phone_number == phone_number,
                Guest.hotel_id == hotel_id
            )
        )
        guest = result.scalar_one_or_none()
        
        if not guest:
            guest = Guest(
                phone_number=phone_number,
                hotel_id=hotel_id
            )
            session.add(guest)
            await session.commit()
            await session.refresh(guest)
        
        return guest

async def save_message(conversation_id: str, direction: str, content: str, intent: str = None, response_time_ms: int = None):
    async with AsyncSessionLocal() as session:
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            intent=intent,
            response_time_ms=response_time_ms
        )
        session.add(message)
        await session.commit()
        return message