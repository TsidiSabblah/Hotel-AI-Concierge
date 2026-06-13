from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from app.db import AsyncSessionLocal
from app.db import Business, BusinessUser, BusinessKnowledge
from sqlalchemy import select
import uuid
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/business", tags=["business"])
security = HTTPBasic()
bearer_security = HTTPBearer()


# ============ HELPER FUNCTION ============
async def get_current_business(credentials: HTTPAuthorizationCredentials = Depends(bearer_security)):
    """Validate bearer token and return business_id (simplified for now)"""
    token = credentials.credentials
    # In production, validate against stored tokens or decode JWT
    # For now, just return a placeholder
    # TODO: Implement proper token validation
    return {"business_id": "from_token", "token": token}


# ============ LOGIN ENDPOINT ============
@router.post("/login")
async def business_login(credentials: HTTPBasicCredentials = Depends(security)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BusinessUser).where(BusinessUser.email == credentials.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if credentials.password != user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = secrets.token_urlsafe(32)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "business_id": user.business_id,
            "name": user.name,
            "role": user.role,
            "message": "Login successful"
        }


# ============ BUSINESS CRUD ============
@router.get("/")
async def get_businesses():
    """List all businesses (super admin)"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Business))
        businesses = result.scalars().all()
        return [
            {
                "id": b.id,
                "name": b.name,
                "type": b.type,
                "whatsapp_number": b.whatsapp_number,
                "city": b.city,
                "is_active": b.is_active
            }
            for b in businesses
        ]


@router.post("/")
async def create_business(data: dict):
    """Create a new business"""
    async with AsyncSessionLocal() as session:
        business = Business(
            id=str(uuid.uuid4()),
            name=data["name"],
            type=data.get("type", "hotel"),
            whatsapp_number=data["whatsapp_number"],
            address=data.get("address"),
            city=data.get("city"),
            settings=data.get("settings", {})
        )
        session.add(business)
        await session.commit()
        await session.refresh(business)
        return {"id": business.id, "name": business.name}


@router.get("/{business_id}")
async def get_business(business_id: str):
    """Get a single business"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        return {
            "id": business.id,
            "name": business.name,
            "type": business.type,
            "whatsapp_number": business.whatsapp_number,
            "address": business.address,
            "city": business.city,
            "settings": business.settings,
            "is_active": business.is_active
        }


# ============ CONVERSATIONS ============
@router.get("/{business_id}/conversations")
async def get_business_conversations(business_id: str, limit: int = 50):
    """Get recent conversations for a business"""
    from app.db import Conversation, Guest
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation, Guest)
            .join(Guest, Conversation.guest_id == Guest.id)
            .where(Conversation.business_id == business_id)
            .order_by(Conversation.started_at.desc())
            .limit(limit)
        )
        conversations = []
        for conv, guest in result:
            conversations.append({
                "id": conv.id,
                "guest_name": guest.name or "Anonymous",
                "room_number": guest.room_number,
                "message_count": conv.message_count,
                "started_at": conv.started_at.isoformat() if conv.started_at else None
            })
        return conversations


# ============ BUSINESS KNOWLEDGE (FAQ) ============
@router.get("/{business_id}/knowledge")
async def get_knowledge(business_id: str):
    """Get all FAQ/knowledge for a business"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BusinessKnowledge).where(BusinessKnowledge.business_id == business_id)
        )
        knowledge = result.scalars().all()
        return [
            {
                "id": k.id,
                "category": k.category,
                "question": k.question,
                "answer": k.answer
            }
            for k in knowledge
        ]


@router.post("/{business_id}/knowledge")
async def add_knowledge(business_id: str, data: dict):
    """Add FAQ/knowledge for a business"""
    async with AsyncSessionLocal() as session:
        knowledge = BusinessKnowledge(
            id=str(uuid.uuid4()),
            business_id=business_id,
            category=data.get("category", "general"),
            question=data["question"],
            answer=data["answer"]
        )
        session.add(knowledge)
        await session.commit()
        return {"id": knowledge.id, "message": "Knowledge added"}


@router.put("/{business_id}/knowledge/{knowledge_id}")
async def update_knowledge(business_id: str, knowledge_id: str, data: dict):
    """Update FAQ/knowledge"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BusinessKnowledge).where(
                BusinessKnowledge.id == knowledge_id,
                BusinessKnowledge.business_id == business_id
            )
        )
        knowledge = result.scalar_one_or_none()
        if not knowledge:
            raise HTTPException(status_code=404, detail="Knowledge not found")
        
        knowledge.question = data.get("question", knowledge.question)
        knowledge.answer = data.get("answer", knowledge.answer)
        knowledge.category = data.get("category", knowledge.category)
        
        await session.commit()
        return {"message": "Knowledge updated"}


@router.delete("/{business_id}/knowledge/{knowledge_id}")
async def delete_knowledge(business_id: str, knowledge_id: str):
    """Delete FAQ/knowledge"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BusinessKnowledge).where(
                BusinessKnowledge.id == knowledge_id,
                BusinessKnowledge.business_id == business_id
            )
        )
        knowledge = result.scalar_one_or_none()
        if not knowledge:
            raise HTTPException(status_code=404, detail="Knowledge not found")
        
        await session.delete(knowledge)
        await session.commit()
        return {"message": "Knowledge deleted"}


# ============ STATISTICS ============
@router.get("/{business_id}/stats")
async def get_business_stats(business_id: str):
    """Get message volume stats for a business"""
    from app.db import Message, Guest
    
    async with AsyncSessionLocal() as session:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await session.execute(
            select(Message).where(
                Message.business_id == business_id,
                Message.created_at > week_ago
            )
        )
        weekly_messages = len(result.scalars().all())
        
        result = await session.execute(
            select(Guest).where(Guest.business_id == business_id)
        )
        total_guests = len(result.scalars().all())
        
        return {
            "weekly_messages": weekly_messages,
            "total_guests": total_guests,
            "business_id": business_id
        }


# ============ DEBUG ENDPOINTS ============
@router.get("/debug-password/{email}")
async def debug_password(email: str):
    """Debug endpoint to check stored password (remove in production)"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BusinessUser).where(BusinessUser.email == email)
        )
        user = result.scalar_one_or_none()
        if user:
            return {
                "email": user.email,
                "stored_password": user.password_hash,
                "name": user.name
            }
        return {"error": "User not found"}