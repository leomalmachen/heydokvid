"""
Security utilities and middleware
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer
security = HTTPBearer()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for request/response processing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=(), payment=()"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # JWT ID for revocation
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT access token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("JWT decode error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt
    """
    return pwd_context.hash(password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    """
    return secrets.token_urlsafe(length)


class AESCipher:
    """
    AES encryption/decryption for sensitive data
    """
    
    def __init__(self, key: Optional[str] = None):
        self.key = (key or settings.ENCRYPTION_KEY).encode()[:32].ljust(32, b'\0')
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data
        """
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data
        """
        try:
            iv, ct = encrypted_data.split(':')
            iv = base64.b64decode(iv)
            ct = base64.b64decode(ct)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except Exception as e:
            logger.error("Decryption error", error=str(e))
            raise ValueError("Invalid encrypted data")


# Global cipher instance
cipher = AESCipher()


def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data for storage
    """
    return cipher.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data
    """
    return cipher.decrypt(encrypted_data)


def sanitize_input(input_string: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    """
    # Remove null bytes
    sanitized = input_string.replace('\x00', '')
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_room_id(room_id: str) -> bool:
    """
    Validate room ID format
    """
    # Room ID should be alphanumeric with underscores, 16-64 chars
    import re
    pattern = r'^[a-zA-Z0-9_]{16,64}$'
    return bool(re.match(pattern, room_id))


def generate_meeting_token(room_id: str, user_id: str, role: str) -> str:
    """
    Generate secure meeting access token
    """
    data = {
        "room_id": room_id,
        "user_id": user_id,
        "role": role,
        "nonce": generate_secure_token(16),
    }
    
    return create_access_token(data, expires_delta=timedelta(hours=24)) 