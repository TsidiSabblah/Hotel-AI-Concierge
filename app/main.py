from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx import os

from app.admin import setup_admin
from app.db import init_db, get_hotel_by_phone, get_or_create_guest
from app.config import settings
from agents.hotel_agent import HotelAgent
# Initialize AI agent
hotel_agent = HotelAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Hotel AI Concierge...")
    await init_db()
    print("✅ Database ready")
    print(f"🤖 AI Agent: {settings.LLM_MODEL}")
    print(f"📱 Server running at http://localhost:8000")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="Hotel AI Concierge",
    description="AI-powered guest experience for Ghana hotels",
    version="1.0.0",
    lifespan=lifespan
)

# Setup admin panel
setup_admin(app)   

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    phone_number: str
    hotel_phone: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    needs_human: bool

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

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a guest message and return AI response
    """
    try:
        # Get hotel by phone number
        hotel = await get_hotel_by_phone(request.hotel_phone)
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        
        # Get or create guest
        guest = await get_or_create_guest(request.phone_number, hotel.id)
        
        # Process with AI
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
@app.get("/test-simple")
async def test_simple():
    """Simple test to verify AI is responding"""
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured"}
    
    test_message = "What time is breakfast?"
    response = await hotel_agent.simple_chat(test_message)
    return {"status": "ok", "question": test_message, "answer": response}

@app.get("/test-ai")
async def test_ai():
    """Test endpoint to verify AI is working"""
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured in .env file"}
    
    test_message = "What time is breakfast?"
    hotel_context = {"name": "Test Hotel Accra", "city": "Accra"}
    
    result = await hotel_agent.process_message(test_message, hotel_context)
    return {"status": "ok", "test_result": result}
@app.get("/debug-ai")
async def debug_ai():
    """Debug endpoint to see raw AI response"""
    import traceback
    from agents.hotel_agent import HotelAgent
    
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "placeholder_get_from_groq.com":
        return {"status": "error", "message": "GROQ_API_KEY not configured"}
    
    agent = HotelAgent()
    test_message = "What time is breakfast?"
    hotel_context = {"name": "Test Hotel", "city": "Accra"}
    
    try:
        # Call the AI directly without any parsing
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
import httpx
from app.config import settings

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("📨 Full webhook payload received")

        # --- Extract message from Meta Cloud API format (used by 360dialog) ---
        messages = []
        # Direct 'messages' field
        if "messages" in body:
            messages = body["messages"]
        else:
            # Drill down into entry[0].changes[0].value.messages
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
            print("⚠️ No messages found in payload")
            return {"status": "ok"}

        msg = messages[0]
        sender = msg.get("from")
        text = msg.get("text", {}).get("body", "")

        if not sender or not text:
            print(f"⚠️ Missing sender or text: sender={sender}, text={text}")
            return {"status": "ok"}

        print(f"✅ Processing message from {sender}: '{text}'")

        # --- Call your AI agent ---
        hotel_context = {"name": "Test Hotel", "city": "Accra"}
        result = await hotel_agent.process_message(
            message=text,
            hotel_context=hotel_context,
            guest_name=sender
        )
        reply_text = result.get("response", "I'm sorry, I didn't understand that.")
        print(f"🤖 AI reply: {reply_text}")

        # --- Send reply via 360dialog API ---
        api_key = settings.DIALOG_API_KEY
        if not api_key:
            print("❌ DIALOG_API_KEY is not set in environment variables")
            return {"status": "error", "detail": "Missing API key"}

        print(f"🔑 Using API key: {api_key[:10]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://waba-sandbox.360dialog.io/v1/messages",
                headers={
                    "D360-API-KEY": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": sender,
                    "type": "text",
                    "text": {"body": reply_text}
                }
            )
            if response.status_code == 201:
                print("✅ Reply sent successfully")
            else:
                print(f"❌ Failed to send reply: {response.status_code} - {response.text}")

        return {"status": "ok"}

    except Exception as e:
        print(f"🔥 Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/debug-key")
async def debug_key():
    from app.config import settings
    return {
        "has_key": bool(settings.DIALOG_API_KEY),
        "key_prefix": settings.DIALOG_API_KEY[:10] if settings.DIALOG_API_KEY else None,
        "env_var": os.getenv("DIALOG_API_KEY") is not None
    }