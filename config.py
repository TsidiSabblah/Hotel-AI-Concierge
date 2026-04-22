from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Force load .env file
load_dotenv()

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Hotel AI Concierge"
    DEBUG: bool = True
    
    # Database - SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./hotel_concierge.db"
    
    # WhatsApp
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "test_verify_token"
    
    # SMS (Arkesel - Ghana)
    ARKESEL_API_KEY: Optional[str] = None
    ARKESEL_SENDER_ID: str = "HotelConcierge"
    
    # LLM - Groq (get from environment)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    # Payment
    HUBTEL_CLIENT_ID: Optional[str] = None
    HUBTEL_CLIENT_SECRET: Optional[str] = None
    
    # Hotel PMS
    HOTELRUNNER_API_KEY: Optional[str] = None
    HOTELRUNNER_PROPERTY_ID: Optional[int] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Debug print
print(f"🔑 GROQ_API_KEY loaded: {settings.GROQ_API_KEY[:10]}...{settings.GROQ_API_KEY[-5:] if settings.GROQ_API_KEY else 'NOT FOUND'}")
print(f"🤖 Model: {settings.LLM_MODEL}")