from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Hotel AI Concierge"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./hotel_concierge.db"
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "test_verify_token"
    ARKESEL_API_KEY: Optional[str] = None
    ARKESEL_SENDER_ID: str = "HotelConcierge"
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    HUBTEL_CLIENT_ID: Optional[str] = None
    HUBTEL_CLIENT_SECRET: Optional[str] = None
    HOTELRUNNER_API_KEY: Optional[str] = None
    HOTELRUNNER_PROPERTY_ID: Optional[int] = None
    DIALOG_API_KEY: Optional[str] = os.getenv("DIALOG_API_KEY")  # ← MOVED INSIDE

    class Config:  # ← INDENTED INSIDE Settings class
        env_file = ".env"
        extra = "ignore"

settings = Settings()
print(f"GROQ_API_KEY: {settings.GROQ_API_KEY[:15] if settings.GROQ_API_KEY else 'NOT SET'}...")
print(f"Model: {settings.LLM_MODEL}")