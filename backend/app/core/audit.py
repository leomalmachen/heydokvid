"""
Audit logging middleware for HIPAA compliance
"""

import json
import time
from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog

from app.core.database import AsyncSessionLocal
from app.models.audit import AuditLog, AuditAction
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests for HIPAA compliance
    """
    
    # Endpoints to exclude from audit logging
    EXCLUDED_PATHS = {"/health", "/metrics", "/api/docs", "/api/openapi.json"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip audit for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        request_id = getattr(request.state, "request_id", None)
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Capture request body for POST/PUT/PATCH
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request._body = body  # Store for later use
                if body:
                    request_body = body.decode("utf-8")[:1000]  # Limit size
            except Exception:
                pass
        
        # Process request
        response = None
        error_message = None
        success = True
        
        try:
            response = await call_next(request)
            success = response.status_code < 400
        except Exception as e:
            error_message = str(e)
            success = False
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log audit entry
            await self._create_audit_log(
                user_id=user_id,
                action=self._get_action_from_method(method),
                resource_type=self._get_resource_type(path),
                resource_id=self._get_resource_id(path),
                ip_address=client_ip,
                user_agent=user_agent,
                request_id=request_id,
                success=success,
                error_message=error_message,
                metadata={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code if response else None,
                    "duration_ms": round(duration * 1000, 2),
                    "request_body": request_body,
                }
            )
        
        return response
    
    async def _create_audit_log(
        self,
        user_id: Optional[str],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str],
        ip_address: Optional[str],
        user_agent: str,
        request_id: Optional[str],
        success: bool,
        error_message: Optional[str],
        metadata: dict
    ):
        """
        Create audit log entry in database
        """
        try:
            async with AsyncSessionLocal() as session:
                audit_log = AuditLog(
                    user_id=UUID(user_id) if user_id else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=UUID(resource_id) if resource_id and self._is_valid_uuid(resource_id) else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    success=success,
                    error_message=error_message,
                    metadata=metadata
                )
                session.add(audit_log)
                await session.commit()
                
                # Also log to structured logger
                logger.info(
                    "audit_log",
                    user_id=user_id,
                    action=action.value,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    success=success,
                    duration_ms=metadata.get("duration_ms"),
                    status_code=metadata.get("status_code")
                )
        except Exception as e:
            logger.error("Failed to create audit log", error=str(e))
    
    def _get_action_from_method(self, method: str) -> AuditAction:
        """
        Map HTTP method to audit action
        """
        mapping = {
            "GET": AuditAction.READ,
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE,
        }
        return mapping.get(method, AuditAction.READ)
    
    def _get_resource_type(self, path: str) -> str:
        """
        Extract resource type from path
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api":
            return parts[2]  # e.g., /api/v1/rooms -> rooms
        return "unknown"
    
    def _get_resource_id(self, path: str) -> Optional[str]:
        """
        Extract resource ID from path
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 4 and parts[0] == "api":
            return parts[3]  # e.g., /api/v1/rooms/123 -> 123
        return None
    
    def _is_valid_uuid(self, value: str) -> bool:
        """
        Check if string is valid UUID
        """
        try:
            UUID(value)
            return True
        except ValueError:
            return False


async def create_audit_entry(
    session: AsyncSession,
    user_id: Optional[UUID],
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """
    Helper function to create audit log entries
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        error_message=error_message,
        metadata=metadata or {}
    )
    
    session.add(audit_log)
    await session.flush()
    
    return audit_log 