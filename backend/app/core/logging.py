"""
Structured logging configuration for HIPAA/GDPR compliance
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging with audit trail support
    """
    # Configure Python logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Create formatter based on settings
    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for audit logs
    if settings.ENVIRONMENT == "production":
        file_handler = logging.FileHandler("/app/logs/audit.log")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_app_context,
            mask_sensitive_data,
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_app_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add application context to all log entries
    """
    event_dict["app"] = settings.APP_NAME
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["version"] = settings.VERSION
    
    # Add request context if available
    from structlog.contextvars import get_contextvars
    context = get_contextvars()
    
    if "request_id" in context:
        event_dict["request_id"] = context["request_id"]
    
    if "user_id" in context:
        event_dict["user_id"] = context["user_id"]
    
    if "ip_address" in context:
        event_dict["ip_address"] = context["ip_address"]
    
    return event_dict


def mask_sensitive_data(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in logs for GDPR compliance
    """
    sensitive_fields = [
        "password", "token", "secret", "api_key", "email",
        "phone", "ssn", "credit_card", "bank_account"
    ]
    
    def mask_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        masked = {}
        for key, value in d.items():
            if any(field in key.lower() for field in sensitive_fields):
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [mask_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                masked[key] = value
        return masked
    
    return mask_dict(event_dict)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a configured logger instance
    """
    return structlog.get_logger(name) 