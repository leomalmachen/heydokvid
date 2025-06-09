import os
from typing import Optional, List

# Simple configuration class without Pydantic Settings
class Settings:
    """Application settings with validation"""
    
    def __init__(self):
        # App Configuration
        self.app_name = "HeyDok Video API"
        self.version = "1.0.0"
        self.environment = "development"
        self.debug = False
        
        # Server Configuration
        self.host = "0.0.0.0"
        self.port = 8000
        self.app_url = None
        
        # Database Configuration
        self.database_url = "sqlite:///./heydok.db"
        
        # LiveKit Configuration - HARDCODED FOR TESTING
        self.livekit_url = "wss://heydok-5pbd24sq.livekit.cloud"
        self.livekit_api_key = "APIysK82G8HGmFr"
        self.livekit_api_secret = "ytVhapnJwHIzfQzzqZL3sPbSJfelfdBcCtD2vCwm0bbA"
        
        # Security Configuration
        self.allowed_origins = ["*"]
        self.api_key = None
        self.secret_key = "your-secret-key-change-in-production"
        
        # File Upload Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_file_types = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]
        self.upload_dir = "uploads"
        
        # Meeting Configuration
        self.max_participants_per_meeting = 10
        self.meeting_duration_hours = 24
        self.cleanup_interval_minutes = 60
        
        # Logging Configuration
        self.log_level = "INFO"
        
        # External API Configuration
        self.rate_limit_per_minute = 60
        
        # Validate settings
        self._validate()
    
    def _validate(self):
        """Validate settings"""
        if not self.livekit_url.startswith(("ws://", "wss://")):
            raise ValueError("LIVEKIT_URL must start with ws:// or wss://")
        
        if self.environment not in ["development", "staging", "production"]:
            raise ValueError("Environment must be one of: development, staging, production")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins with app URL if available"""
        origins = self.allowed_origins.copy()
        
        if self.app_url and self.app_url not in origins:
            origins.extend([
                self.app_url,
                self.app_url.rstrip('/'),
            ])
        
        # Add development origins in non-production
        if not self.is_production:
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "https://localhost:3000", 
                "https://localhost:8000"
            ]
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)
        
        return origins

# Create global settings instance
try:
    settings = Settings()
    print("✅ Configuration loaded successfully")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print("Please check your environment variables and .env file")
    raise

# Export commonly used values
DATABASE_URL = settings.database_url
LIVEKIT_URL = settings.livekit_url
LIVEKIT_API_KEY = settings.livekit_api_key
LIVEKIT_API_SECRET = settings.livekit_api_secret
IS_PRODUCTION = settings.is_production
IS_DEVELOPMENT = settings.is_development

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def validate_required_settings():
    """Validate that all required settings are properly configured"""
    errors = []
    
    # Check LiveKit configuration
    if not settings.livekit_url:
        errors.append("LIVEKIT_URL is required")
    if not settings.livekit_api_key:
        errors.append("LIVEKIT_API_KEY is required")
    if not settings.livekit_api_secret:
        errors.append("LIVEKIT_API_SECRET is required")
    
    # Check security in production
    if settings.is_production:
        if settings.secret_key == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed in production")
        if "*" in settings.allowed_origins:
            errors.append("ALLOWED_ORIGINS should not contain '*' in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

# Validate settings on import
validate_required_settings() 