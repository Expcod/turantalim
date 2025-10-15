import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Configuration class for TuranTalim bot"""
    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Webhook settings
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH: str = "/telegram-webhook/"
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "localhost")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    
    # Django API settings
    DJANGO_API_URL: str = os.getenv("DJANGO_API_URL", "")
    DJANGO_API_KEY: str = os.getenv("DJANGO_API_KEY", "")
    
    # Admin settings
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Teacher group settings
    TEACHER_GROUP_ID: int = int(os.getenv("TEACHER_GROUP_ID", "0"))
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///turan_talim.db")
    
    # Validate configuration
    @classmethod
    def validate(cls) -> bool:
        """Validate if all required settings are provided"""
        if not cls.BOT_TOKEN:
            print("ERROR: BOT_TOKEN is not set in environment variables")
            return False
            
        if not cls.DJANGO_API_URL:
            print("ERROR: DJANGO_API_URL is not set in environment variables")
            return False
            
        if not cls.DJANGO_API_KEY:
            print("ERROR: DJANGO_API_KEY is not set in environment variables")
            return False
            
        if cls.TEACHER_GROUP_ID == 0:
            print("WARNING: TEACHER_GROUP_ID is not set properly")
            
        return True
