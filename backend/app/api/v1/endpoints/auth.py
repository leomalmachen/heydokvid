"""
Authentication API endpoints
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, encrypt_sensitive_data
from app.core.audit import create_audit_entry
from app.models.user import User
from app.models.audit import AuditAction
from app.schemas.auth import TokenRequest, TokenResponse
from app.core.config import settings

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login(
    credentials: TokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Login with external ID and API key
    """
    # Get user by external ID
    user = await db.scalar(
        select(User).where(User.external_id == credentials.external_id)
    )
    
    if not user:
        # Create audit log for failed login
        await create_audit_entry(
            db,
            user_id=None,
            action=AuditAction.READ,
            resource_type="auth",
            resource_id=None,
            success=False,
            error_message="User not found",
            metadata={"external_id": credentials.external_id}
        )
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify API key (in production, this would check against heydok's API)
    # For now, we'll do a simple check
    if credentials.api_key != settings.SECRET_KEY[:32]:  # Temporary check
        # Create audit log for failed login
        await create_audit_entry(
            db,
            user_id=user.id,
            action=AuditAction.READ,
            resource_type="auth",
            resource_id=user.id,
            success=False,
            error_message="Invalid API key"
        )
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    
    # Update last login
    user.update_last_login()
    
    # Create audit log for successful login
    await create_audit_entry(
        db,
        user_id=user.id,
        action=AuditAction.READ,
        resource_type="auth",
        resource_id=user.id,
        success=True,
        metadata={"action": "login"}
    )
    
    await db.commit()
    
    expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at
    ) 