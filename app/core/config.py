"""
Application configuration
"""

import os
from typing import List


class Settings:
    """
    Application settings with environment variable support
    """
    
    # Application
    APP_NAME: str = "Heydok Video"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "https://f2f9-217-138-216-222.ngrok-free.app",
        "https://video-meeting-app-two.vercel.app"
    ]
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8001")
    
    # LiveKit - Updated with Cloud Configuration
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "APIM4pxPvXu6uF4")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A")
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "wss://malmachen-8s6xtzpq.livekit.cloud")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./heydok_video.db")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Prometheus
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "False").lower() == "true"
    
    # Allowed hosts
    ALLOWED_HOSTS: List[str] = ["*"]


# Create settings instance
settings = Settings() 