import os
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./heydok.db")

# Fix for Heroku Postgres URL if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, unique=True, nullable=False)
    host_name = Column(String, nullable=False)
    host_role = Column(String, default="doctor")
    external_id = Column(String, nullable=True)
    patient_name = Column(String, nullable=True)
    patient_joined = Column(Boolean, default=False)
    patient_setup_completed = Column(Boolean, default=False)
    document_uploaded = Column(Boolean, default=False)
    media_test_completed = Column(Boolean, default=False)
    meeting_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    last_patient_status = Column(String, nullable=True)
    last_status_update = Column(DateTime, nullable=True)
    metadata = Column(JSON, default=dict)

class PatientDocument(Base):
    __tablename__ = "patient_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, unique=True, nullable=False)
    meeting_id = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    status = Column(String, default="uploaded")

class MediaTest(Base):
    __tablename__ = "media_tests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String, unique=True, nullable=False)
    meeting_id = Column(String, nullable=False)
    has_camera = Column(Boolean, nullable=False)
    has_microphone = Column(Boolean, nullable=False)
    camera_working = Column(Boolean, nullable=False)
    microphone_working = Column(Boolean, nullable=False)
    patient_confirmed = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    allowed_to_join = Column(Boolean, default=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cleanup expired meetings
def cleanup_expired_meetings():
    """Remove meetings older than 24 hours"""
    db = SessionLocal()
    try:
        expired_meetings = db.query(Meeting).filter(
            Meeting.expires_at < datetime.utcnow()
        ).all()
        
        for meeting in expired_meetings:
            # Delete related documents and media tests
            db.query(PatientDocument).filter(
                PatientDocument.meeting_id == meeting.meeting_id
            ).delete()
            
            db.query(MediaTest).filter(
                MediaTest.meeting_id == meeting.meeting_id
            ).delete()
            
            db.delete(meeting)
        
        db.commit()
        return len(expired_meetings)
    finally:
        db.close() 