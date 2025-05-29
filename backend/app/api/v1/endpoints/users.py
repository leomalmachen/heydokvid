"""
Users API endpoints
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import encrypt_sensitive_data
from app.core.audit import create_audit_entry
from app.models.user import User
from app.models.audit import AuditAction
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    CurrentUserResponse
)
from app.api.deps import get_current_user, get_current_admin_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=UserResponse)
@limiter.limit("5/minute")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """
    Create a new user (admin only)
    """
    # Check if user already exists
    existing_user = await db.scalar(
        select(User).where(
            (User.email == user_data.email) | 
            (User.external_id == user_data.external_id)
        )
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or external ID already exists"
        )
    
    # Create user with encrypted name
    user = User(
        external_id=user_data.external_id,
        email=user_data.email,
        role=user_data.role,
        encrypted_name=encrypt_sensitive_data(user_data.name),
        metadata=user_data.metadata
    )
    
    db.add(user)
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id=user.id,
        metadata={"created_user_email": user.email}
    )
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> CurrentUserResponse:
    """
    Get current user information
    """
    return CurrentUserResponse(
        id=current_user.id,
        external_id=current_user.external_id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        metadata=current_user.metadata,
        can_create_rooms=current_user.can_create_rooms,
        can_record=current_user.can_record
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> UserListResponse:
    """
    List users with pagination (admin only)
    """
    # Build query
    query = select(User)
    
    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(User.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get user details
    """
    # Users can get their own info, admins can get any user
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user"
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.READ,
        resource_type="user",
        resource_id=user.id
    )
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Update user details
    """
    # Users can update their own info (limited), admins can update any user
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user"
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Non-admins can only update certain fields
    update_data = user_update.dict(exclude_unset=True)
    if not current_user.is_admin:
        # Limit fields that non-admins can update
        allowed_fields = {"metadata"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    # Update fields
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user.id,
        metadata={"updated_fields": list(update_data.keys())}
    )
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> dict:
    """
    Delete a user (admin only)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete - just deactivate
    user.is_active = False
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="user",
        resource_id=user.id
    )
    
    await db.commit()
    
    return {"message": "User deactivated successfully"} 