"""
Enhanced security middleware and authentication for HIPAA/GDPR compliance
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import uuid
import time
import jwt
import structlog
from functools import wraps
import asyncio
from collections import defaultdict

from app.core.config import settings
from app.models.user import User

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security middleware for headers, request ID, and audit logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request for audit trail
        start_time = time.time()
        
        logger.info("Request started",
                   request_id=request_id,
                   method=request.method,
                   url=str(request.url),
                   client_ip=request.client.host,
                   user_agent=request.headers.get("user-agent"))
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error("Request failed",
                        request_id=request_id,
                        error=str(e),
                        duration=time.time() - start_time)
            raise
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Add security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
        
        # GDPR compliance headers
        response.headers["X-Data-Processing"] = "medical-consultation"
        response.headers["X-Retention-Policy"] = "7-years-hipaa"
        
        # Log response
        logger.info("Request completed",
                   request_id=request_id,
                   status_code=response.status_code,
                   duration=duration)
        
        return response


def rate_limit(calls: int, period: int):
    """
    Rate limiting decorator
    
    Args:
        calls: Number of allowed calls
        period: Time period in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('http_request') or kwargs.get('request')
            
            if request:
                client_ip = request.client.host
                now = time.time()
                
                # Clean old entries
                rate_limit_storage[client_ip] = [
                    timestamp for timestamp in rate_limit_storage[client_ip]
                    if now - timestamp < period
                ]
                
                # Check rate limit
                if len(rate_limit_storage[client_ip]) >= calls:
                    logger.warning("Rate limit exceeded",
                                 client_ip=client_ip,
                                 calls=len(rate_limit_storage[client_ip]),
                                 limit=calls)
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Max {calls} calls per {period} seconds."
                    )
                
                # Add current request
                rate_limit_storage[client_ip].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user from JWT token (optional - returns None if no token)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # In a real implementation, fetch user from database
        # For now, return a mock user based on token data
        user_data = payload.get("user_data", {})
        
        # Create user object from token data
        user = User(
            id=user_id,
            external_id=user_data.get("external_id"),
            email=user_data.get("email"),
            role=user_data.get("role", "patient"),
            encrypted_name=user_data.get("name", ""),
            is_active=True
        )
        
        return user
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        return None
    except Exception as e:
        logger.error("Error validating token", error=str(e))
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current user from JWT token (required)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(required_role: str):
    """
    Decorator to require specific user role
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role.value != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}


class GDPRComplianceMiddleware(BaseHTTPMiddleware):
    """
    GDPR compliance middleware for data processing logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Log data processing activities for GDPR compliance
        if request.method in ["POST", "PUT", "PATCH"]:
            logger.info("Data processing activity",
                       request_id=getattr(request.state, 'request_id', 'unknown'),
                       method=request.method,
                       endpoint=request.url.path,
                       client_ip=request.client.host,
                       purpose="medical-video-consultation",
                       legal_basis="consent-and-medical-care")
        
        response = await call_next(request)
        return response


def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    """
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length
    return sanitized[:max_length].strip()


def validate_meeting_id(meeting_id: str) -> bool:
    """
    Validate meeting ID format for security
    """
    if not meeting_id:
        return False
    
    # Check format: xxx-xxxx-xxx (alphanumeric with dashes)
    import re
    pattern = r'^[a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3}$'
    return bool(re.match(pattern, meeting_id))


def log_security_event(event_type: str, details: Dict[str, Any], request: Optional[Request] = None):
    """
    Log security events for audit trail
    """
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    if request:
        log_data.update({
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent")
        })
    
    logger.warning("Security event", **log_data)


# HIPAA compliance utilities
def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging (HIPAA compliance)
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def is_sensitive_endpoint(path: str) -> bool:
    """
    Check if endpoint handles sensitive medical data
    """
    sensitive_patterns = [
        "/meetings/",
        "/recordings/",
        "/users/",
        "/auth/"
    ]
    
    return any(pattern in path for pattern in sensitive_patterns) 