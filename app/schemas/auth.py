"""
Authentication schemas for API validation
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Schema for token request"""
    external_id: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class ValidateTokenRequest(BaseModel):
    """Schema for validating meeting token"""
    token: str = Field(..., min_length=1)


class ValidateTokenResponse(BaseModel):
    """Schema for token validation response"""
    valid: bool
    room_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[datetime] = None 