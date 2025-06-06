from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import Meeting, PatientDocument, MediaTest, get_db
from utils.exceptions import (
    MeetingNotFoundError, 
    MeetingExpiredError,
    MeetingFullError,
    ValidationError
)
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class MeetingService:
    """Service for managing meetings with business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_meeting(
        self, 
        host_name: str, 
        host_role: str = "doctor",
        external_id: Optional[str] = None
    ) -> Meeting:
        """Create a new meeting"""
        
        # Generate unique meeting ID
        meeting_id = self._generate_meeting_id()
        
        # Create meeting record
        meeting = Meeting(
            meeting_id=meeting_id,
            host_name=host_name,
            host_role=host_role,
            external_id=external_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=settings.meeting_duration_hours)
        )
        
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        
        logger.info(
            f"Meeting created successfully",
            extra={
                "meeting_id": meeting_id,
                "host_name": host_name,
                "host_role": host_role,
                "external_id": external_id
            }
        )
        
        return meeting
    
    def get_meeting(self, meeting_id: str, check_expired: bool = True) -> Meeting:
        """Get meeting by ID with optional expiration check"""
        
        meeting = self.db.query(Meeting).filter(
            Meeting.meeting_id == meeting_id
        ).first()
        
        if not meeting:
            raise MeetingNotFoundError(meeting_id)
        
        if check_expired and meeting.expires_at < datetime.utcnow():
            raise MeetingExpiredError(meeting_id)
        
        return meeting
    
    def get_meeting_status(self, meeting_id: str) -> Dict[str, Any]:
        """Get comprehensive meeting status"""
        
        meeting = self.get_meeting(meeting_id)
        
        # Count documents
        doc_count = self.db.query(PatientDocument).filter(
            PatientDocument.meeting_id == meeting_id
        ).count()
        
        # Count media tests
        test_count = self.db.query(MediaTest).filter(
            MediaTest.meeting_id == meeting_id
        ).count()
        
        return {
            "meeting_id": meeting.meeting_id,
            "doctor_name": meeting.host_name,
            "patient_name": meeting.patient_name,
            "patient_joined": meeting.patient_joined,
            "patient_setup_completed": meeting.patient_setup_completed,
            "document_uploaded": meeting.document_uploaded,
            "documents_count": doc_count,
            "media_test_completed": meeting.media_test_completed,
            "media_tests_count": test_count,
            "meeting_active": meeting.meeting_active,
            "created_at": meeting.created_at.isoformat(),
            "expires_at": meeting.expires_at.isoformat(),
            "last_patient_status": meeting.last_patient_status,
            "last_status_update": meeting.last_status_update.isoformat() if meeting.last_status_update else None,
            "external_id": meeting.external_id
        }
    
    def update_patient_status(
        self, 
        meeting_id: str, 
        patient_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> Meeting:
        """Update patient status in meeting"""
        
        meeting = self.get_meeting(meeting_id)
        
        # Update fields if provided
        if patient_name:
            meeting.patient_name = patient_name
        
        if status:
            meeting.last_patient_status = status
            meeting.last_status_update = datetime.utcnow()
            
            # Update meeting flags based on status
            if status == "patient_active":
                meeting.patient_joined = True
            elif status == "in_meeting":
                meeting.meeting_active = True
        
        self.db.commit()
        self.db.refresh(meeting)
        
        logger.info(
            f"Patient status updated",
            extra={
                "meeting_id": meeting_id,
                "patient_name": patient_name,
                "status": status
            }
        )
        
        return meeting
    
    def mark_patient_setup_completed(self, meeting_id: str) -> Meeting:
        """Mark patient setup as completed"""
        
        meeting = self.get_meeting(meeting_id)
        meeting.patient_setup_completed = True
        
        self.db.commit()
        self.db.refresh(meeting)
        
        return meeting
    
    def mark_document_uploaded(self, meeting_id: str) -> Meeting:
        """Mark document as uploaded"""
        
        meeting = self.get_meeting(meeting_id)
        meeting.document_uploaded = True
        
        self.db.commit()
        self.db.refresh(meeting)
        
        return meeting
    
    def mark_media_test_completed(self, meeting_id: str) -> Meeting:
        """Mark media test as completed"""
        
        meeting = self.get_meeting(meeting_id)
        meeting.media_test_completed = True
        
        self.db.commit()
        self.db.refresh(meeting)
        
        return meeting
    
    def get_active_meetings(self, limit: int = 100) -> List[Meeting]:
        """Get list of active (non-expired) meetings"""
        
        return self.db.query(Meeting).filter(
            Meeting.expires_at > datetime.utcnow()
        ).limit(limit).all()
    
    def get_meetings_by_external_id(self, external_id: str) -> List[Meeting]:
        """Get meetings by external ID"""
        
        return self.db.query(Meeting).filter(
            Meeting.external_id == external_id
        ).all()
    
    def cleanup_expired_meetings(self) -> int:
        """Clean up expired meetings and return count"""
        
        expired_meetings = self.db.query(Meeting).filter(
            Meeting.expires_at < datetime.utcnow()
        ).all()
        
        count = 0
        for meeting in expired_meetings:
            # Delete related documents
            self.db.query(PatientDocument).filter(
                PatientDocument.meeting_id == meeting.meeting_id
            ).delete()
            
            # Delete related media tests
            self.db.query(MediaTest).filter(
                MediaTest.meeting_id == meeting.meeting_id
            ).delete()
            
            # Delete meeting
            self.db.delete(meeting)
            count += 1
        
        self.db.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired meetings")
        
        return count
    
    def _generate_meeting_id(self) -> str:
        """Generate unique meeting ID"""
        import random
        import string
        
        while True:
            # Generate random ID
            meeting_id = 'mtg_' + ''.join(
                random.choices(string.ascii_lowercase + string.digits, k=12)
            )
            
            # Check if it exists
            existing = self.db.query(Meeting).filter(
                Meeting.meeting_id == meeting_id
            ).first()
            
            if not existing:
                return meeting_id

def get_meeting_service(db: Session = None) -> MeetingService:
    """Factory function to get meeting service"""
    if db is None:
        db = next(get_db())
    return MeetingService(db) 