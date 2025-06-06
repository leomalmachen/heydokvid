from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class HeyDokException(Exception):
    """Base exception for HeyDok application"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        extra_data: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.extra_data = extra_data or {}
        super().__init__(message)

class ValidationError(HeyDokException):
    """Raised when input validation fails"""
    pass

class MeetingError(HeyDokException):
    """Base exception for meeting-related errors"""
    pass

class MeetingNotFoundError(MeetingError):
    """Raised when a meeting cannot be found"""
    
    def __init__(self, meeting_id: str):
        super().__init__(
            f"Meeting mit ID '{meeting_id}' nicht gefunden",
            error_code="MEETING_NOT_FOUND",
            extra_data={"meeting_id": meeting_id}
        )

class MeetingExpiredError(MeetingError):
    """Raised when trying to access an expired meeting"""
    
    def __init__(self, meeting_id: str):
        super().__init__(
            f"Meeting '{meeting_id}' ist abgelaufen",
            error_code="MEETING_EXPIRED", 
            extra_data={"meeting_id": meeting_id}
        )

class MeetingFullError(MeetingError):
    """Raised when a meeting has reached participant limit"""
    
    def __init__(self, meeting_id: str, max_participants: int):
        super().__init__(
            f"Meeting '{meeting_id}' hat bereits die maximale Teilnehmerzahl ({max_participants}) erreicht",
            error_code="MEETING_FULL",
            extra_data={"meeting_id": meeting_id, "max_participants": max_participants}
        )

class LiveKitError(HeyDokException):
    """Base exception for LiveKit-related errors"""
    pass

class LiveKitConnectionError(LiveKitError):
    """Raised when LiveKit connection fails"""
    
    def __init__(self, details: str = None):
        super().__init__(
            f"LiveKit-Verbindung fehlgeschlagen: {details or 'Unbekannter Fehler'}",
            error_code="LIVEKIT_CONNECTION_ERROR",
            extra_data={"details": details}
        )

class TokenGenerationError(LiveKitError):
    """Raised when token generation fails"""
    
    def __init__(self, participant_name: str, room_name: str, details: str = None):
        super().__init__(
            f"Token-Generierung für '{participant_name}' in Raum '{room_name}' fehlgeschlagen",
            error_code="TOKEN_GENERATION_ERROR",
            extra_data={
                "participant_name": participant_name,
                "room_name": room_name,
                "details": details
            }
        )

class PatientError(HeyDokException):
    """Base exception for patient-related errors"""
    pass

class DocumentUploadError(PatientError):
    """Raised when document upload fails"""
    
    def __init__(self, filename: str, reason: str):
        super().__init__(
            f"Dokument-Upload für '{filename}' fehlgeschlagen: {reason}",
            error_code="DOCUMENT_UPLOAD_ERROR",
            extra_data={"filename": filename, "reason": reason}
        )

class MediaTestError(PatientError):
    """Raised when media test fails"""
    
    def __init__(self, meeting_id: str, reason: str):
        super().__init__(
            f"Media-Test für Meeting '{meeting_id}' fehlgeschlagen: {reason}",
            error_code="MEDIA_TEST_ERROR",
            extra_data={"meeting_id": meeting_id, "reason": reason}
        )

class ConfigurationError(HeyDokException):
    """Raised when configuration is invalid"""
    
    def __init__(self, config_key: str, expected: str = None):
        message = f"Konfigurationsfehler: '{config_key}' ist nicht gesetzt oder ungültig"
        if expected:
            message += f". Erwartet: {expected}"
            
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            extra_data={"config_key": config_key, "expected": expected}
        )

def exception_to_http_exception(exc: HeyDokException) -> HTTPException:
    """Convert HeyDok exception to FastAPI HTTPException"""
    
    # Map exception types to HTTP status codes
    status_map = {
        MeetingNotFoundError: status.HTTP_404_NOT_FOUND,
        MeetingExpiredError: status.HTTP_410_GONE,
        MeetingFullError: status.HTTP_409_CONFLICT,
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DocumentUploadError: status.HTTP_400_BAD_REQUEST,
        MediaTestError: status.HTTP_400_BAD_REQUEST,
        LiveKitConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
        TokenGenerationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    # Default to 500 for unknown exceptions
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log the exception
    logger.error(
        f"Exception occurred: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "extra_data": exc.extra_data,
            "exception_type": type(exc).__name__
        }
    )
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": exc.error_code,
            "message": exc.message,
            "extra_data": exc.extra_data
        }
    )

def handle_unexpected_exception(exc: Exception, context: str = None) -> HTTPException:
    """Handle unexpected exceptions with proper logging"""
    
    context_info = f" in {context}" if context else ""
    
    logger.error(
        f"Unexpected exception{context_info}: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "context": context
        }
    )
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error_code": "INTERNAL_ERROR",
            "message": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
            "extra_data": {"context": context} if context else {}
        }
    ) 