"""
Audit middleware for logging requests
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import structlog

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Audit middleware for request logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=round(duration, 3),
            request_id=getattr(request.state, "request_id", None)
        )
        
        return response 