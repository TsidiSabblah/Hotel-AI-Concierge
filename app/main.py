from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
import uuid

from app.api_business import router as business_router
from app.admin import setup_admin
from app.db import init_db, get_hotel_by_phone, get_or_create_guest
from app.db import AsyncSessionLocal, Business, BusinessKnowledge, BusinessUser
from app.config import settings
from agents.hotel_agent import HotelAgent
from sqlalchemy import select, insert

# Initialize AI agent
hotel_agent = HotelAgent()


# ============ SEED FUNCTION ============
async def seed_businesses():
    """Add sample businesses if none exist"""
    async with AsyncSessionLocal() as session:
        # Check if businesses table has data
        result = await session.execute(select(Business))
        existing = result.scalars().first()
        if existing:
            print("✅ Businesses already exist, skipping seed")
            return

        print("🌱 Seeding sample businesses...")

        # Insert sample businesses
        biz1 = Business(
            id=str(uuid.uuid4()),
            name="Royal Serenity Hotel",
            type="hotel",
            whatsapp_number="551146733492",
            city="Accra"
        )
        biz2 = Business(
            id=str(uuid.uuid4()),
            name="Ocean View Apartments",
            type="apartment",
            whatsapp_number="551146733493",
            city="Accra"
        )
        session.add_all([biz1, biz2])
        await session.commit()

        # Add sample knowledge
        await session.execute(
            insert(BusinessKnowledge).values([
                {
                    "id": str(uuid.uuid4()),
                    "business_id": biz1.id,
                    "category": "breakfast",
                    "question": "What time is breakfast?",
                    "answer": "Breakfast is 6:30-10:30 AM at Palm Court Restaurant"
                },
                {
                    "id": str(uuid.uuid4()),
                    "business_id": biz2.id,
                    "category": "wifi",
                    "question": "What is the WiFi password?",
                    "answer": "WiFi: OceanView2025"
                },
            ])
        )
        await session.commit()

        # ============ CREATE TEST MANAGER USER ============
        result = await session.execute(
            select(BusinessUser).where(BusinessUser.email == "manager@royalserenity.com")
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            test_user = BusinessUser(
                id=str(uuid.uuid4()),
                business_id=biz1.id,
                email="manager@royalserenity.com",
                password_hash="hotel123",
                name="John Mensah",
                role="manager"
            )
            session.add(test_user)
            await session.commit()
            print("✅ Test manager user created.")
        else:
            print("ℹ️ Test manager user already exists, skipping creation.")

        print("✅ Sample businesses and knowledge added")


# ============ HELPER FUNCTION ============
async def send_whatsapp_reply(to: str, message: str):
    """Send WhatsApp reply via 360dialog"""
    api_key = settings.DIALOG_API_KEY
    if not api_key:
        print("❌ DIALOG_API_KEY not set")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://waba-sandbox.360dialog.io/v1/messages",
            headers={
                "D360-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
        )
        if response.status_code == 201:
            print("✅ Reply sent")
        else:
            print(f"❌ Failed: {response.text}")


# ============ LIFESPAN FUNCTION ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Hotel AI Concierge...")
    await init_db()
    await seed_businesses()
    print("✅ Database ready")
    print(f"🤖 AI Agent: {settings.LLM_MODEL}")
    print(f"📱 Server running at http://localhost:8000")
    yield
    print("👋 Shutting down...")


# ============ FASTAPI APP ============
app = FastAPI(
    title="Hotel AI Concierge",
    description="AI-powered guest experience for Ghana hotels",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(business_router)

# Setup admin panel
setup_admin(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ HTML ROUTES ============
@app.get("/manager-login", response_class=HTMLResponse)
async def manager_login():
    with open("app/manager_login.html", "r") as f:
        return f.read()

@app.get("/manager-dashboard", response_class=HTMLResponse)
async def manager_dashboard():
    with open("app/manager_dashboard.html", "r") as f:
        return f.read()


# ============ REQUEST/RESPONSE MODELS ============
class ChatRequest(BaseModel):
    message: str
    phone_number: str
    hotel_phone: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    needs_human: bool


# ============ ROOT ENDPOINTS ============
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Hotel AI Concierge",
        "message": "Welcome to Ghana's first AI hotel concierge",
        "database": "SQLite (working without Docker)",
        "ai_agent": "ready" if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "placeholder_get_from_groq.com" else "needs API key"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}


# ============ CHAT ENDPOINT ============
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        hotel = await get_hotel_by_phone(request.hotel_phone)
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        
        guest = await get_or_create_guest(request.phone_number, hotel.id)
        
        hotel_context = {
            "name": hotel.name,
            "city": hotel.city,
            "id": hotel.id
        }
        
        result = await hotel_agent.process_message(
            message=request.message,
            hotel_context=hotel_context,
            guest_name=guest.name or "Guest"
        )
        
        return ChatResponse(
            response=result.get("response", "Thank you for your message. How else can I assist you?"),
            intent=result.get("intent", "general_question"),
            needs_human=result.get("needs_human", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ TEST ENDPOINTS ============
@app.get("/test-simple")
async def test_simple():
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured"}
    
    test_message = "What time is breakfast?"
    response = await hotel_agent.simple_chat(test_message)
    return {"status": "ok", "question": test_message, "answer": response}

@app.get("/test-ai")
async def test_ai():
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured in .env file"}
    
    test_message = "What time is breakfast?"
    hotel_context = {"name": "Test Hotel Accra", "city": "Accra"}
    result = await hotel_agent.process_message(test_message, hotel_context)
    return {"status": "ok", "test_result": result}

@app.get("/debug-ai")
async def debug_ai():
    import traceback
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured"}
    
    agent = HotelAgent()
    test_message = "What time is breakfast?"
    
    try:
        response = agent.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": f"Answer briefly: {test_message}"}],
            temperature=0.7,
            max_tokens=100
        )
        raw_result = response.choices[0].message.content
        return {
            "status": "ok",
            "raw_response": raw_result,
            "model": settings.LLM_MODEL,
            "api_key_prefix": settings.GROQ_API_KEY[:10] + "..."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@app.get("/debug-key")
async def debug_key():
    return {
        "has_key": bool(settings.DIALOG_API_KEY),
        "key_prefix": settings.DIALOG_API_KEY[:10] if settings.DIALOG_API_KEY else None,
        "env_var": os.getenv("DIALOG_API_KEY") is not None
    }


@app.get("/super-login", response_class=HTMLResponse)
async def super_login():
    with open("app/super_login.html", "r") as f:
        return f.read()

@app.get("/super-dashboard", response_class=HTMLResponse)
async def super_dashboard():
    with open("app/super_dashboard.html", "r") as f:
        return f.read()


# ============ WEBHOOK ENDPOINT ============
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("📨 Full webhook payload received")

        messages = []
        if "messages" in body:
            messages = body["messages"]
        else:
            entries = body.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    if "messages" in value:
                        messages = value["messages"]
                        break
                if messages:
                    break

        if not messages:
            print("⚠️ No messages found")
            return {"status": "ok"}

        msg = messages[0]
        sender = msg.get("from")
        text = msg.get("text", {}).get("body", "")

        if not sender or not text:
            return {"status": "ok"}

        metadata = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {})
        business_phone_raw = metadata.get("display_phone_number", "")
        business_phone = business_phone_raw.replace(" ", "").replace("-", "").replace("+", "")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Business).where(Business.whatsapp_number.contains(business_phone))
            )
            business = result.scalar_one_or_none()

            if not business:
                print(f"⚠️ No business found for number: {business_phone_raw}")
                reply_text = "Thank you for your message. Our team will get back to you shortly."
                await send_whatsapp_reply(sender, reply_text)
                return {"status": "ok"}

            result = await session.execute(
                select(BusinessKnowledge).where(BusinessKnowledge.business_id == business.id)
            )
            knowledge_items = result.scalars().all()

            hotel_context = {
                "name": business.name,
                "type": business.type,
                "city": business.city,
                "knowledge": [
                    {"question": k.question, "answer": k.answer}
                    for k in knowledge_items
                ]
            }

        print(f"✅ Processing for business: {business.name}")
        print(f"✅ Message from {sender}: '{text}'")

        result = await hotel_agent.process_message(
            message=text,
            hotel_context=hotel_context,
            guest_name=sender
        )
        reply_text = result.get("response", "How may I assist you?")
        await send_whatsapp_reply(sender, reply_text)

        return {"status": "ok"}

    except Exception as e:
        print(f"🔥 Webhook error: {e}")
        return {"status": "error", "detail": str(e)}