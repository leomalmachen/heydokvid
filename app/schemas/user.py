"""
User schemas for API validation
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    role: UserRole
    metadata: dict = Field(default_factory=dict)


class UserCreate(UserBase):
    """Schema for creating a user"""
    external_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        # Basic name validation
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    external_id: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response"""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


class CurrentUserResponse(UserResponse):
    """Schema for current user response with additional info"""
    can_create_rooms: bool
    can_record: bool
    
    class Config:
        orm_mode = True
        from_attributes = True 