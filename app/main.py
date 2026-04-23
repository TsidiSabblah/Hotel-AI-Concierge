from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
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
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Receive messages from WhatsApp mock server"""
    try:
        body = await request.json()
        print(f"📨 WhatsApp webhook received: {body}")
        
        # Extract message from the mock server format
        message_text = None
        sender = None
        
        # The mock server might send different formats
        if "message" in body:
            message_text = body.get("message", {}).get("text", "")
            sender = body.get("from", "")
        elif "text" in body:
            message_text = body.get("text", "")
            sender = body.get("from", "")
        elif "body" in body:
            message_text = body.get("body", "")
            sender = body.get("sender", "")
        
        if message_text:
            # Use your existing hotel agent
            hotel_context = {"name": "Test Hotel", "city": "Accra"}
            result = await hotel_agent.process_message(
                message=message_text,
                hotel_context=hotel_context,
                guest_name=sender or "Guest"
            )
            
            response_text = result.get("response", "How may I assist you?")
            print(f"🤖 AI response: {response_text}")
            
            # Return in format mock server expects
            return {"reply": response_text}
        
        return {"status": "ok", "message": "No text message found"}
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}
@app.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: int = None
):
    """WhatsApp webhook verification"""
    if hub_mode == "subscribe" and hub_verify_token == "test_verify_token":
        return Response(content=str(hub_challenge), media_type="text/plain")
    return {"error": "Verification failed"}
# Setup admin panel
setup_admin(app)