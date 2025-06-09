"""
Document Service for handling patient document operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from database import PatientDocument
from utils.exceptions import DocumentNotFoundError, DocumentProcessingError
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for managing patient documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(
        self,
        document_id: str,
        meeting_id: str,
        patient_name: str,
        filename: str,
        content_type: str,
        file_size: int,
        content: bytes
    ) -> PatientDocument:
        """Create a new patient document"""
        try:
            document = PatientDocument(
                id=document_id,
                meeting_id=meeting_id,
                patient_name=patient_name,
                filename=filename,
                content_type=content_type,
                file_size=file_size,
                content=content,
                uploaded_at=datetime.utcnow(),
                processed=False
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document created: {document_id} for meeting {meeting_id}")
            return document
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document: {e}")
            raise DocumentProcessingError(f"Failed to create document: {e}")
    
    def get_document(self, document_id: str) -> Optional[PatientDocument]:
        """Get a document by ID"""
        try:
            return self.db.query(PatientDocument).filter(
                PatientDocument.id == document_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    def get_documents_for_meeting(self, meeting_id: str) -> List[PatientDocument]:
        """Get all documents for a meeting"""
        try:
            return self.db.query(PatientDocument).filter(
                PatientDocument.meeting_id == meeting_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting documents for meeting {meeting_id}: {e}")
            return []
    
    def has_documents_for_meeting(self, meeting_id: str) -> bool:
        """Check if a meeting has any documents"""
        try:
            count = self.db.query(PatientDocument).filter(
                PatientDocument.meeting_id == meeting_id
            ).count()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking documents for meeting {meeting_id}: {e}")
            return False
    
    def process_document(self, document_id: str) -> bool:
        """Process a document (placeholder for actual processing logic)"""
        try:
            document = self.get_document(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document {document_id} not found")
            
            # Placeholder for actual document processing
            # In production: OCR, validation, data extraction, etc.
            document.processed = True
            document.processed_at = datetime.utcnow()
            document.processing_result = {"status": "processed", "extracted_data": {}}
            
            self.db.commit()
            logger.info(f"Document processed: {document_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing document {document_id}: {e}")
            raise DocumentProcessingError(f"Failed to process document: {e}")
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            self.db.delete(document)
            self.db.commit()
            logger.info(f"Document deleted: {document_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def cleanup_expired_documents(self, days: int = 30) -> int:
        """Clean up documents older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            expired_docs = self.db.query(PatientDocument).filter(
                PatientDocument.uploaded_at < cutoff_date
            ).all()
            
            count = len(expired_docs)
            for doc in expired_docs:
                self.db.delete(doc)
            
            self.db.commit()
            logger.info(f"Cleaned up {count} expired documents")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired documents: {e}")
            return 0 