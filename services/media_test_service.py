"""
Media Test Service for handling patient media test operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from database import MediaTest
from utils.exceptions import MediaTestNotFoundError, MediaTestProcessingError
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MediaTestService:
    """Service for managing patient media tests"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_media_test(
        self,
        test_id: str,
        meeting_id: str,
        has_camera: bool,
        has_microphone: bool,
        camera_working: bool,
        microphone_working: bool,
        patient_confirmed: bool,
        allowed_to_join: bool
    ) -> MediaTest:
        """Create a new media test"""
        try:
            media_test = MediaTest(
                test_id=test_id,
                meeting_id=meeting_id,
                has_camera=has_camera,
                has_microphone=has_microphone,
                camera_working=camera_working,
                microphone_working=microphone_working,
                patient_confirmed=patient_confirmed,
                allowed_to_join=allowed_to_join
            )
            
            self.db.add(media_test)
            self.db.commit()
            self.db.refresh(media_test)
            
            logger.info(f"Media test created: {test_id} for meeting {meeting_id}")
            return media_test
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating media test: {e}")
            raise MediaTestProcessingError(f"Failed to create media test: {e}")
    
    def get_media_test(self, test_id: str) -> Optional[MediaTest]:
        """Get a media test by ID"""
        try:
            return self.db.query(MediaTest).filter(
                MediaTest.test_id == test_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting media test {test_id}: {e}")
            return None
    
    def get_media_tests_for_meeting(self, meeting_id: str) -> List[MediaTest]:
        """Get all media tests for a meeting"""
        try:
            return self.db.query(MediaTest).filter(
                MediaTest.meeting_id == meeting_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting media tests for meeting {meeting_id}: {e}")
            return []
    
    def get_latest_media_test_for_meeting(self, meeting_id: str) -> Optional[MediaTest]:
        """Get the latest media test for a meeting"""
        try:
            return self.db.query(MediaTest).filter(
                MediaTest.meeting_id == meeting_id
            ).order_by(MediaTest.timestamp.desc()).first()
        except Exception as e:
            logger.error(f"Error getting latest media test for meeting {meeting_id}: {e}")
            return None
    
    def has_successful_media_test(self, meeting_id: str) -> bool:
        """Check if a meeting has a successful media test"""
        try:
            test = self.db.query(MediaTest).filter(
                MediaTest.meeting_id == meeting_id,
                MediaTest.allowed_to_join == True
            ).first()
            return test is not None
        except Exception as e:
            logger.error(f"Error checking media test for meeting {meeting_id}: {e}")
            return False
    
    def update_media_test(
        self,
        test_id: str,
        **kwargs
    ) -> bool:
        """Update a media test"""
        try:
            media_test = self.get_media_test(test_id)
            if not media_test:
                raise MediaTestNotFoundError(f"Media test {test_id} not found")
            
            for key, value in kwargs.items():
                if hasattr(media_test, key):
                    setattr(media_test, key, value)
            
            self.db.commit()
            logger.info(f"Media test updated: {test_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating media test {test_id}: {e}")
            raise MediaTestProcessingError(f"Failed to update media test: {e}")
    
    def delete_media_test(self, test_id: str) -> bool:
        """Delete a media test"""
        try:
            media_test = self.get_media_test(test_id)
            if not media_test:
                return False
            
            self.db.delete(media_test)
            self.db.commit()
            logger.info(f"Media test deleted: {test_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting media test {test_id}: {e}")
            return False
    
    def cleanup_expired_media_tests(self, days: int = 30) -> int:
        """Clean up media tests older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            expired_tests = self.db.query(MediaTest).filter(
                MediaTest.timestamp < cutoff_date
            ).all()
            
            count = len(expired_tests)
            for test in expired_tests:
                self.db.delete(test)
            
            self.db.commit()
            logger.info(f"Cleaned up {count} expired media tests")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired media tests: {e}")
            return 0 