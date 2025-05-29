"""
Application configuration using Pydantic Settings
"""

from typing import List, Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation
    """
    # Application
    APP_NAME: str = "Heydok Video"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str
    REDIS_POOL_SIZE: int = 10
    
    # LiveKit
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_URL: str
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    ENCRYPTION_KEY: str = Field(..., min_length=32)
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://d321-169-150-197-59.ngrok-free.app"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Features
    ENABLE_RECORDING: bool = True
    ENABLE_CHAT: bool = True
    MAX_PARTICIPANTS: int = 20
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Session
    SESSION_LIFETIME_MINUTES: int = 1440
    
    # Audit Log
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years for HIPAA
    
    # Recording
    RECORDING_STORAGE_PATH: str = "/var/lib/heydok/recordings"
    RECORDING_MAX_SIZE_GB: int = 10
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "Heydok Video <noreply@heydok.com>"
    SMTP_TLS: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    
    # TURN Server
    TURN_DOMAIN: Optional[str] = None
    TURN_USERNAME: Optional[str] = None
    TURN_PASSWORD: Optional[str] = None
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("SENTRY_DSN")
    def validate_sentry_dsn(cls, v, values):
        if v and values.get("ENVIRONMENT") == "production":
            return v
        return None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        # Field validation
        validate_assignment = True
        
        # Extra fields are forbidden
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings() 