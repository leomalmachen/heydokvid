import os
from typing import Optional, List
from pydantic import BaseSettings, validator, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # App Configuration
    app_name: str = Field(default="HeyDok Video API", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    app_url: Optional[str] = Field(default=None, env="APP_URL")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./heydok.db", env="DATABASE_URL")
    
    # LiveKit Configuration
    livekit_url: str = Field(..., env="LIVEKIT_URL")  # Required
    livekit_api_key: str = Field(..., env="LIVEKIT_API_KEY")  # Required
    livekit_api_secret: str = Field(..., env="LIVEKIT_API_SECRET")  # Required
    
    # Security Configuration
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # File Upload Configuration
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=["pdf", "jpg", "jpeg", "png", "doc", "docx"], 
        env="ALLOWED_FILE_TYPES"
    )
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    
    # Meeting Configuration
    max_participants_per_meeting: int = Field(default=10, env="MAX_PARTICIPANTS_PER_MEETING")
    meeting_duration_hours: int = Field(default=24, env="MEETING_DURATION_HOURS")
    cleanup_interval_minutes: int = Field(default=60, env="CLEANUP_INTERVAL_MINUTES")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # External API Configuration
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    @validator("database_url")
    def fix_postgres_url(cls, v):
        """Fix Heroku Postgres URL if needed"""
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v
    
    @validator("livekit_url")
    def validate_livekit_url(cls, v):
        """Validate LiveKit URL format"""
        if not v:
            raise ValueError("LIVEKIT_URL is required")
        if not (v.startswith("ws://") or v.startswith("wss://")):
            raise ValueError("LIVEKIT_URL must start with ws:// or wss://")
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True) 
    def parse_allowed_file_types(cls, v):
        """Parse comma-separated file types"""
        if isinstance(v, str):
            return [ft.strip().lower() for ft in v.split(",")]
        return [ft.lower() for ft in v] if isinstance(v, list) else v
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
try:
    settings = Settings()
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