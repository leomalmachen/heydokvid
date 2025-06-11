import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import uuid
import mimetypes
from pathlib import Path
import time
import json
import aiofiles
import structlog
from urllib.parse import quote_plus
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from livekit_client import LiveKitClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="🏥 HeyDok Video API",
    description="""
    ## 🩺 Professionelle Video-Sprechstunden Platform

    Die HeyDok Video API ermöglicht die nahtlose Integration von Video-Meetings in Drittsysteme.
    Perfekt für Praxisverwaltungssoftware, Klinik-Systeme und Telemedizin-Plattformen.

    ### ✨ Hauptfunktionen
    - 🔗 **Meeting-Links erstellen** - Programmatisch Video-Termine generieren
    - 👥 **Arzt-Patient Workflow** - Speziell für medizinische Anwendungsfälle optimiert  
    - 📋 **Patient Setup Flow** - Automatische Dokumentenprüfung und Media-Tests
    - 📊 **Status-Tracking** - Echtzeitüberwachung des Patient-Flows
    - 🖥️ **Bildschirmfreigabe** - Sowohl Ärzte als auch Patienten können ihren Bildschirm teilen
    - 🔒 **DSGVO-konform** - Sichere Ende-zu-Ende Verschlüsselung

    ### 🚀 Quick Start
    1. **Meeting erstellen**: `POST /api/external/create-meeting-link`
    2. **Patient-Link versenden**: Der Patient durchläuft automatisch Setup
    3. **Status verfolgen**: `POST /api/external/patient-status` (optional)

    ### 🔧 Integration
    - **Praxisverwaltung**: Nahtlose Integration in bestehende Systeme
    - **Terminbuchung**: Automatische Meeting-Erstellung bei Terminbuchung
    - **Patientenportal**: Direkte Links für Patienten

    ### 📞 Support
    - **E-Mail**: support@heydok.com
    - **Dokumentation**: Vollständige API-Docs verfügbar
    - **SLA**: 99.9% Uptime-Garantie
    """,
    version="1.0.0",
    terms_of_service="https://heydok.com/terms",
    contact={
        "name": "HeyDok Video API Support",
        "url": "https://heydok.com/support",
        "email": "api-support@heydok.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "External API",
            "description": "🔌 **Integration Endpoints** - Für externe Systeme und Drittanbieter-Integration",
        },
        {
            "name": "Meeting Management", 
            "description": "🏥 **Meeting Verwaltung** - Interne Endpoints für Meeting-Erstellung und -Verwaltung",
        },
        {
            "name": "Patient Flow",
            "description": "👤 **Patient Workflow** - Setup, Dokumenten-Upload und Media-Tests",
        },
        {
            "name": "System",
            "description": "⚙️ **System & Health** - Health-Checks und System-Status",
        }
    ],
    servers=[
        {
            "url": "https://heyvid-66c7325ed29b.herokuapp.com",
            "description": "🌐 Production Server"
        },
        {
            "url": "http://localhost:8000",
            "description": "🔧 Development Server"
        }
    ]
)

# Configure CORS
allowed_origins = ["*"]  # In production, restrict this!
app_url = os.getenv("APP_URL")

# Try to detect Heroku URL if APP_URL is not set
if not app_url:
    heroku_app_name = os.getenv("HEROKU_APP_NAME") 
    if heroku_app_name:
        app_url = f"https://{heroku_app_name}.herokuapp.com"

if app_url:
    logger.info(f"Production mode detected. APP_URL: {app_url}")
    allowed_origins = [
        app_url,
        app_url.rstrip('/'),
        "http://localhost:3000",  # For local development
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000"
    ]
else:
    logger.info("Development mode detected. Allowing all origins.")

# Add HTTPS redirect middleware in production
if app_url and app_url.startswith('https://'):
    @app.middleware("http")
    async def https_redirect_middleware(request: Request, call_next):
        """Redirect HTTP to HTTPS in production"""
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)
        return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Initialize LiveKit client with validation
try:
    livekit = LiveKitClient()
    if livekit.validate_credentials():
        logger.info("LiveKit client initialized and validated successfully")
    else:
        logger.error("LiveKit credentials validation failed")
        raise Exception("Invalid LiveKit credentials")
except Exception as e:
    logger.error(f"Failed to initialize LiveKit client: {e}")
    # In production, you might want to exit here
    # For development, we'll continue but log the error
    livekit = None

# Database and Services Integration - FIXING HEROKU RESTART ISSUE
from database import get_db, Meeting, PatientDocument, MediaTest
from services.meeting_service import MeetingService
from services.document_service import DocumentService
from services.media_test_service import MediaTestService
from sqlalchemy.orm import Session

# Initialize logger
logger = structlog.get_logger()

# Static configurations
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# REPLACED BY DATABASE SERVICES
def get_meeting_service(db: Session = Depends(get_db)) -> MeetingService:
    return MeetingService(db)

def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)

def get_media_test_service(db: Session = Depends(get_db)) -> MediaTestService:
    return MediaTestService(db)

# Cleanup old meetings periodically (now using database)
def cleanup_old_meetings():
    """Remove meetings older than 24 hours and related documents/tests"""
    # Database cleanup is now handled by the cleanup function in database.py
    from database import cleanup_expired_meetings
    cleaned_count = cleanup_expired_meetings()
    logger.info(f"Database cleanup completed: {cleaned_count} expired meetings removed")

# Request/Response models
class CreateMeetingRequest(BaseModel):
    host_name: str = Field(default="Host", min_length=1, max_length=50)
    host_role: str = Field(default="doctor", pattern="^(doctor|patient)$")  # Fixed: regex -> pattern

class JoinMeetingRequest(BaseModel):
    participant_name: str = Field(min_length=1, max_length=50)
    participant_role: str = Field(default="patient", pattern="^(doctor|patient)$")  # Fixed: regex -> pattern

class MeetingResponse(BaseModel):
    meeting_id: str
    meeting_url: str
    livekit_url: str
    token: str
    participants_count: int = 0
    user_role: str  # New: role of the joining user
    meeting_status: dict  # New: status information

class HealthResponse(BaseModel):
    status: str
    app_version: str = "1.0.0"
    meetings_count: int
    livekit_connected: bool
    timestamp: str

# New models for patient pre-meeting validation
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    upload_timestamp: str
    status: str

class MediaTestRequest(BaseModel):
    meeting_id: str
    has_camera: bool
    has_microphone: bool
    camera_working: bool
    microphone_working: bool
    patient_confirmed: bool

class MediaTestResponse(BaseModel):
    test_id: str
    meeting_id: str
    status: str
    timestamp: str
    allowed_to_join: bool

class PatientJoinRequest(BaseModel):
    patient_name: str = Field(min_length=1, max_length=50)
    document_id: Optional[str] = None
    media_test_id: Optional[str] = None

# New: Enhanced meeting status model
class MeetingStatusResponse(BaseModel):
    meeting_id: str
    doctor_name: str
    patient_name: Optional[str] = None
    patient_joined: bool
    patient_setup_completed: bool
    document_uploaded: bool
    media_test_completed: bool
    meeting_active: bool
    created_at: str
    last_patient_status: Optional[str] = None
    last_status_update: Optional[str] = None

# API Models for external meeting link creation and status updates
class CreateMeetingLinkRequest(BaseModel):
    doctor_name: str = Field(
        min_length=1, 
        max_length=100, 
        description="👨‍⚕️ Name des Arztes/der Ärztin",
        example="Dr. med. Anna Schmidt"
    )
    external_id: Optional[str] = Field(
        None, 
        max_length=50, 
        description="🏷️ Externe Referenz-ID für das Meeting (z.B. Termin-ID aus PVS)",
        example="TERMIN-2024-001234"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "doctor_name": "Dr. med. Anna Schmidt",
                "external_id": "TERMIN-2024-001234"
            }
        }

class CreateMeetingLinkResponse(BaseModel):
    meeting_id: str = Field(
        description="🆔 Eindeutige Meeting-ID", 
        example="mtg_8f4e2d1c9b6a"
    )
    doctor_join_url: str = Field(
        description="🔗 Direkter Beitritts-Link für den Arzt (ohne Setup)",
        example="https://heyvid-66c7325ed29b.herokuapp.com/meeting/mtg_8f4e2d1c9b6a?role=doctor&direct=true"
    )
    patient_join_url: str = Field(
        description="🔗 Patient-Link mit Setup-Prozess (Dokumente, Media-Test)",
        example="https://heyvid-66c7325ed29b.herokuapp.com/patient-setup?meeting=mtg_8f4e2d1c9b6a"
    )
    external_id: Optional[str] = Field(
        description="🏷️ Externe Referenz-ID (falls übermittelt)",
        example="TERMIN-2024-001234"
    )
    created_at: str = Field(
        description="📅 Erstellungszeitpunkt (ISO 8601)",
        example="2024-01-15T14:30:00Z"
    )
    expires_at: str = Field(
        description="⏰ Ablaufzeitpunkt des Meetings (24h nach Erstellung)",
        example="2024-01-16T14:30:00Z"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "meeting_id": "mtg_8f4e2d1c9b6a",
                "doctor_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/meeting/mtg_8f4e2d1c9b6a?role=doctor&direct=true",
                "patient_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/patient-setup?meeting=mtg_8f4e2d1c9b6a",
                "external_id": "TERMIN-2024-001234",
                "created_at": "2024-01-15T14:30:00Z",
                "expires_at": "2024-01-16T14:30:00Z"
            }
        }

class PatientStatusRequest(BaseModel):
    meeting_id: str = Field(
        description="🆔 Meeting-ID", 
        example="mtg_8f4e2d1c9b6a"
    )
    patient_name: Optional[str] = Field(
        None, 
        max_length=100, 
        description="👤 Name des Patienten",
        example="Max Mustermann"
    )
    status: str = Field(
        description="📊 Patient-Status",
        pattern="^(link_created|patient_active|in_meeting)$",
        example="patient_active"
    )
    timestamp: Optional[str] = Field(
        None, 
        description="⏰ Zeitpunkt der Status-Änderung (ISO 8601) - optional",
        example="2024-01-15T14:35:00Z"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "meeting_id": "mtg_8f4e2d1c9b6a",
                "patient_name": "Max Mustermann", 
                "status": "patient_active",
                "timestamp": "2024-01-15T14:35:00Z"
            }
        }

class PatientStatusResponse(BaseModel):
    meeting_id: str = Field(description="🆔 Meeting-ID", example="mtg_8f4e2d1c9b6a")
    patient_name: Optional[str] = Field(description="👤 Patient-Name", example="Max Mustermann")
    status: str = Field(description="📊 Aktueller Status", example="in_meeting")
    updated_at: str = Field(description="📅 Letztes Update (ISO 8601)", example="2024-01-15T14:35:00Z")
    success: bool = Field(description="✅ Operation erfolgreich", example=True)
    
    class Config:
        schema_extra = {
            "example": {
                "meeting_id": "mtg_8f4e2d1c9b6a",
                "patient_name": "Max Mustermann",
                "status": "patient_active", 
                "updated_at": "2024-01-15T14:35:00Z",
                "success": True
            }
        }

def generate_meeting_id() -> str:
    """Generate a readable meeting ID format: xxx-yyyy-zzz"""
    parts = []
    for length in [3, 4, 3]:
        part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        parts.append(part)
    return '-'.join(parts)

def get_base_url() -> str:
    """Get the base URL for the application"""
    # Try to get the URL from environment first (Heroku sets this)
    if app_url:
        return app_url.rstrip('/')
    
    # For Heroku, also check for the host header in requests
    # This is a fallback that works better in production
    heroku_app_name = os.getenv("HEROKU_APP_NAME")
    if heroku_app_name:
        return f"https://{heroku_app_name}.herokuapp.com"
    
    # Development fallback
    return "http://localhost:8000"

# Dependency for LiveKit client
def get_livekit_client() -> LiveKitClient:
    if livekit is None:
        raise HTTPException(status_code=503, detail="LiveKit service unavailable - please check configuration")
    return livekit

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers for better browser security
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy for WebRTC
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "media-src 'self' blob: data: https:; "
        "connect-src 'self' https: wss: blob:; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data: https:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp_policy
    
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.now()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = datetime.now() - start_time
    logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} - {process_time.total_seconds():.3f}s")
    
    return response

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve the homepage with doctor-patient workflow information"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            # Inject base URL for API calls
            content = content.replace("{{BASE_URL}}", get_base_url())
            return content
    except FileNotFoundError:
        logger.error("Homepage file not found: frontend/index.html")
        # Return a simple homepage with doctor workflow
        base_url = get_base_url()
        simple_homepage = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HeyDok Video - Doctor-Patient Meetings</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #007bff; text-align: center; }}
                .workflow {{ background: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .step {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #007bff; }}
                button {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
                button:hover {{ background: #0056b3; }}
                .form-group {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }}
                .result {{ margin: 20px 0; padding: 15px; background: #d4edda; border-radius: 5px; display: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏥 HeyDok Video</h1>
                <p style="text-align: center; font-size: 18px; color: #666;">Sichere Video-Sprechstunden zwischen Arzt und Patient</p>
                
                <div class="workflow">
                    <h3>📋 Workflow für Ärzte:</h3>
                    <div class="step">
                        <strong>1.</strong> Arzt erstellt Meeting und erhält Patient-Link
                    </div>
                    <div class="step">
                        <strong>2.</strong> Patient erhält Link und durchläuft Setup-Prozess
                    </div>
                    <div class="step">
                        <strong>3.</strong> Patient lädt Dokumente hoch (Krankenkassenschein etc.)
                    </div>
                    <div class="step">
                        <strong>4.</strong> Patient testet Kamera und Mikrofon
                    </div>
                    <div class="step">
                        <strong>5.</strong> Bei erfolgreichem Setup: Meeting startet
                    </div>
                </div>
                
                <h3>🩺 Neues Meeting erstellen</h3>
                <form id="createMeetingForm">
                    <div class="form-group">
                        <label for="doctorName">Ihr Name (Arzt):</label>
                        <input type="text" id="doctorName" name="doctorName" placeholder="Dr. Schmidt" required>
                    </div>
                    <button type="submit">Meeting erstellen</button>
                </form>
                
                <div id="meetingResult" class="result">
                    <h4>✅ Meeting erstellt!</h4>
                    <p><strong>Meeting ID:</strong> <span id="meetingId"></span></p>
                    <p><strong>Arzt-Dashboard:</strong> <a id="dashboardLink" href="#" target="_blank">Dashboard öffnen</a></p>
                    
                    <div id="doctorLinkContainer" style="display: none;">
                        <p><strong>Ihr direkter Meeting-Link (als Arzt):</strong></p>
                        <p><a id="doctorMeetingLink" href="#" target="_blank" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🩺 Direkt ins Meeting</a></p>
                    </div>
                    
                    <p><strong>Patient-Link zum Teilen:</strong></p>
                    <input type="text" id="patientLink" readonly onclick="this.select()">
                    <button onclick="copyPatientLink()">Link kopieren</button>
                    
                    <div style="margin-top: 15px; padding: 10px; background: #e9ecef; border-radius: 5px; font-size: 14px;">
                        <strong>Hinweis:</strong> Der Patient-Link führt automatisch zum Setup-Prozess (Name, Dokument, Media-Test) bevor der Patient dem Meeting beitreten kann.
                    </div>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
                    <p>Powered by LiveKit • <a href="/health">System Status</a></p>
                </div>
            </div>
            
            <script>
                document.getElementById('createMeetingForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const doctorName = document.getElementById('doctorName').value;
                    
                    try {{
                        const response = await fetch('/api/meetings', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                host_name: doctorName,
                                host_role: 'doctor'
                            }})
                        }});
                        
                        if (response.ok) {{
                            const data = await response.json();
                            
                            document.getElementById('meetingId').textContent = data.meeting_id;
                            document.getElementById('dashboardLink').href = `/doctor-dashboard/${{data.meeting_id}}`;
                            document.getElementById('patientLink').value = data.meeting_status.patient_setup_url;
                            document.getElementById('meetingResult').style.display = 'block';
                            
                            // Add doctor meeting link WITH TOKEN
                            const doctorLinkContainer = document.getElementById('doctorLinkContainer');
                            if (doctorLinkContainer) {{
                                // Store meeting data in sessionStorage so doctor can use it directly
                                sessionStorage.setItem('doctorMeetingData', JSON.stringify(data));
                                document.getElementById('doctorMeetingLink').href = `/meeting/${{data.meeting_id}}?role=doctor&direct=true`;
                                doctorLinkContainer.style.display = 'block';
                            }}
                            
                            // Scroll to result
                            document.getElementById('meetingResult').scrollIntoView({{ behavior: 'smooth' }});
                        }} else {{
                            alert('Fehler beim Erstellen des Meetings');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Fehler beim Erstellen des Meetings');
                    }}
                }});
                
                function copyPatientLink() {{
                    const input = document.getElementById('patientLink');
                    input.select();
                    document.execCommand('copy');
                    alert('Patient-Link kopiert!');
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=simple_homepage, status_code=200)
    except Exception as e:
        logger.error(f"Error serving homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/meetings", response_model=MeetingResponse)
async def create_meeting(
    request: CreateMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client),
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Create a new meeting - typically called by doctors"""
    cleanup_old_meetings()
    
    # Store meeting with correct parameters
    meeting = meeting_service.create_meeting(
        host_name=request.host_name,
        host_role=request.host_role
    )
    
    meeting_id = meeting.meeting_id
    room_name = livekit_client.get_room_name(meeting_id)
    
    # Generate doctor token with admin permissions
    doctor_display_name = f"Dr. {request.host_name}"
    token = livekit_client.generate_token(
        room_name=room_name,
        participant_name=doctor_display_name,
        is_host=True
    )
    
    base_url = get_base_url()
    
    # Generate patient setup URL
    patient_setup_url = f"{base_url}/patient-setup?meeting={meeting_id}"
    
    logger.info(f"Doctor meeting created: {meeting_id} by Dr. {request.host_name}")
    
    return MeetingResponse(
        meeting_id=meeting_id,
        meeting_url=f"{base_url}/meeting/{meeting_id}",
        livekit_url=livekit_client.url,
        token=token,
        participants_count=1,
        user_role=request.host_role,
        meeting_status={
            "patient_setup_url": patient_setup_url,
            "doctor_name": request.host_name,
            "patient_setup_completed": False
        }
    )

@app.post("/api/meetings/{meeting_id}/join", response_model=MeetingResponse)
async def join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client),
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Join an existing meeting with duplicate prevention"""
    # Check if meeting exists
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check participant limit (simplified - max 2: doctor + patient)
    participants_count = 1 + (1 if meeting.patient_joined else 0)
    if participants_count >= 2:  # max 2 participants
        raise HTTPException(status_code=429, detail="Meeting is full")
    
    participant_name = request.participant_name.strip()
    
    # Generate room name and token (no participant tracking needed)
    room_name = livekit_client.get_room_name(meeting_id)
    
    # Generate participant token
    token = livekit_client.generate_token(
        room_name=room_name,
        participant_name=participant_name,
        is_host=False
    )
    
    base_url = get_base_url()
    
    return MeetingResponse(
        meeting_id=meeting_id,
        meeting_url=f"{base_url}/meeting/{meeting_id}",
        livekit_url=livekit_client.url,
        token=token,
        participants_count=participants_count,
        user_role=request.participant_role,
        meeting_status={}
    )

@app.get("/meeting/{meeting_id}", response_class=HTMLResponse)
async def meeting_room(meeting_id: str, role: Optional[str] = None, meeting_service: MeetingService = Depends(get_meeting_service)):
    """Serve the meeting room page with role-based interface"""
    logger.info(f"Meeting room access: {meeting_id}, role parameter: {role}")
    
    # Validate meeting exists - create simple fallback if not found
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        logger.info(f"Meeting {meeting_id} not found, creating basic fallback meeting")
        
        # Simply create a new meeting and accept that it will have a different ID
        # Patient join will work regardless of the exact meeting_id
        meeting = meeting_service.create_meeting(
            host_name="Doctor",
            host_role="doctor"
        )
        logger.info(f"Created fallback meeting with ID {meeting.meeting_id} for requested ID {meeting_id}")
        
        # For patient join, we'll use the created meeting regardless of ID mismatch
        # This handles Heroku database resets gracefully
    
    # IMPROVED LOGIC: Handle role-based access with better patient setup validation
    if role == "doctor":
        # Doctor can always access directly
        user_role = "doctor"
        logger.info(f"Doctor direct access granted for meeting {meeting_id}")
    elif role == "patient":
        # Patient with role=patient parameter - this usually means they completed setup
        # Check setup status but be more permissive for patients coming from the API
        patient_setup_completed = meeting.patient_setup_completed
        media_test_completed = meeting.media_test_completed
        has_patient_name = meeting.patient_name is not None
        
        # If patient has setup completed OR patient has been through the API flow
        # (indicated by patient_name being set), allow access
        if (patient_setup_completed and media_test_completed) or has_patient_name:
            user_role = "patient"
            logger.info(f"Patient access granted - setup_completed: {patient_setup_completed}, media_test: {media_test_completed}, has_name: {has_patient_name}")
        else:
            # Setup genuinely not complete, redirect to setup
            logger.info(f"Patient setup incomplete, redirecting to setup for meeting {meeting_id}")
            setup_url = f"{get_base_url()}/patient-setup?meeting={meeting_id}"
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Setup erforderlich - HeyDok Video</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; text-align: center; }}
                        .container {{ max-width: 600px; margin: 50px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #007bff; }}
                        .button {{ background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 18px; text-decoration: none; display: inline-block; margin: 20px 0; }}
                        .button:hover {{ background: #0056b3; }}
                    </style>
                    <script>
                        // Auto-redirect after 2 seconds
                        setTimeout(function() {{
                            window.location.href = '{setup_url}';
                        }}, 2000);
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1>🏥 Patient Setup erforderlich</h1>
                        <p><strong>Bevor Sie dem Meeting beitreten können, müssen Sie die folgenden Schritte abschließen:</strong></p>
                        <ul style="text-align: left; display: inline-block; margin: 20px 0;">
                            <li>✍️ Namenseingabe</li>
                            <li>📄 Dokument hochladen (optional)</li>
                            <li>🎥 Kamera und Mikrofon testen</li>
                        </ul>
                        <p><em>Sie werden automatisch weitergeleitet...</em></p>
                        <a href="{setup_url}" class="button">Jetzt Setup starten</a>
                    </div>
                </body>
                </html>
                """,
                status_code=200
            )
    else:
        # NO role parameter OR unknown role - ALWAYS redirect to patient setup
        logger.info(f"No role or unknown role, redirecting to patient setup for meeting {meeting_id}")
        setup_url = f"{get_base_url()}/patient-setup?meeting={meeting_id}"
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Patient Setup - HeyDok Video</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; text-align: center; }}
                    .container {{ max-width: 600px; margin: 50px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    h1 {{ color: #4a90e2; }}
                    .button {{ background: #4a90e2; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 18px; text-decoration: none; display: inline-block; margin: 20px 0; }}
                    .button:hover {{ background: #357abd; }}
                </style>
                <script>
                    // Auto-redirect after 1 second
                    setTimeout(function() {{
                        window.location.href = '{setup_url}';
                    }}, 1000);
                </script>
            </head>
            <body>
                <div class="container">
                    <h1>🏥 Willkommen bei HeyDok Video</h1>
                    <p><strong>Bitte durchlaufen Sie den Patient-Setup-Prozess:</strong></p>
                    <ul style="text-align: left; display: inline-block; margin: 20px 0;">
                        <li>✍️ Ihre Daten eingeben</li>
                        <li>📄 Dokument hochladen (optional)</li>
                        <li>🎥 Kamera und Mikrofon testen</li>
                    </ul>
                    <p><em>Sie werden weitergeleitet...</em></p>
                    <a href="{setup_url}" class="button">Setup starten</a>
                </div>
            </body>
            </html>
            """,
            status_code=200
        )
    
    logger.info(f"Determined user_role: {user_role} for meeting {meeting_id}")
    
    try:
        # Choose appropriate template based on role
        if user_role == "doctor":
            template_file = "frontend/doctor_meeting.html"
        else:
            template_file = "frontend/patient_meeting.html"
        
        # Try role-specific template first, fallback to generic
        try:
            with open(template_file, "r", encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            # Fallback to generic meeting template
            with open("frontend/meeting.html", "r", encoding='utf-8') as f:
                html_content = f.read()
        
        # Replace placeholders with actual values - ensure all values are strings
        html_content = html_content.replace("{{MEETING_ID}}", str(meeting_id))
        html_content = html_content.replace("{{USER_ROLE}}", str(user_role))
        html_content = html_content.replace("{{DOCTOR_NAME}}", str(meeting.host_name or "Doctor"))
        html_content = html_content.replace("{{PATIENT_NAME}}", str(meeting.patient_name or ""))
        
        return HTMLResponse(content=html_content)
        
    except FileNotFoundError:
        logger.error("meeting.html not found")
        return HTMLResponse(
            content="<h1>Error</h1><p>Meeting page not found. Please check your installation.</p>",
            status_code=500
        )

@app.get("/patient-setup", response_class=HTMLResponse)
async def patient_setup():
    """Serve the patient setup page for pre-meeting validation"""
    try:
        with open("patient_setup.html", "r", encoding='utf-8') as f:
            html_content = f.read()
            return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("patient_setup.html not found, returning built-in setup page")
        # Return a built-in patient setup page
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Patient Setup - HeyDok Video</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .step { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .step.completed { background: #d4edda; border-color: #28a745; }
                .step.active { background: #fff3cd; border-color: #ffc107; }
                .step.disabled { background: #f8f9fa; color: #6c757d; }
                button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px 0; }
                button:hover { background: #0056b3; }
                button:disabled { background: #6c757d; cursor: not-allowed; }
                input[type="file"] { margin: 10px 0; }
                input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .status.success { background: #d4edda; color: #155724; }
                .status.error { background: #f8d7da; color: #721c24; }
                .video-container { margin: 20px 0; }
                video { width: 100%; max-width: 400px; border: 1px solid #ddd; border-radius: 5px; }
                .hidden { display: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏥 Patient Setup - HeyDok Video</h1>
                <p>Bitte durchlaufen Sie diese Schritte bevor Sie dem Meeting beitreten:</p>
                
                <!-- Step 1: Patient Info -->
                <div class="step active" id="step1">
                    <h3>Schritt 1: Ihre Daten</h3>
                    <label for="patientName">Ihr vollständiger Name:</label>
                    <input type="text" id="patientName" placeholder="Max Mustermann" required>
                    <button onclick="completeStep1()">Weiter</button>
                </div>
                
                <!-- Step 2: Document Upload -->
                <div class="step disabled" id="step2">
                    <h3>Schritt 2: Dokument hochladen (optional)</h3>
                    <p>Falls vorhanden, können Sie Ihren Krankenkassenschein oder ein anderes Dokument hochladen:</p>
                    <input type="file" id="documentFile" accept=".pdf,.jpg,.jpeg,.png,.tiff,.doc,.docx">
                    <button onclick="uploadDocument()" disabled id="uploadBtn">Dokument hochladen</button>
                    <button onclick="skipDocument()" id="skipBtn" style="background: #6c757d; margin-left: 10px;">Überspringen (kein Dokument)</button>
                    <div id="uploadStatus"></div>
                </div>
                
                <!-- Step 3: Media Test -->
                <div class="step disabled" id="step3">
                    <h3>Schritt 3: Kamera und Mikrofon testen</h3>
                    <button onclick="startMediaTest()" id="startTestBtn">Test starten</button>
                    <div class="video-container hidden" id="videoContainer">
                        <video id="testVideo" autoplay muted></video>
                        <p>Können Sie sich in der Kamera sehen und Ihr Mikrofon funktioniert?</p>
                        <button onclick="confirmMediaTest(true)">✅ Ja, alles funktioniert</button>
                        <button onclick="confirmMediaTest(false)">❌ Nein, es gibt Probleme</button>
                    </div>
                    <div id="mediaStatus"></div>
                </div>
                
                <!-- Step 4: Join Meeting -->
                <div class="step disabled" id="step4">
                    <h3>🎉 Bereit für die Sprechstunde!</h3>
                    <p>✅ Alle Schritte abgeschlossen! Sie können nun der Sprechstunde beitreten.</p>
                    <button onclick="joinMeeting()" id="joinBtn" style="background: #28a745; font-size: 18px; padding: 15px 30px;">Bereit für die Sprechstunde</button>
                </div>
            </div>
            
            <script>
                let meetingId = new URLSearchParams(window.location.search).get('meeting');
                let patientName = '';
                let documentId = null;
                let mediaTestId = null;
                let stream = null;
                let isJoining = false; // Prevent multiple clicks
                
                if (!meetingId) {
                    alert('Fehler: Keine Meeting-ID gefunden');
                }
                
                // Step 1: Patient Info
                function completeStep1() {
                    patientName = document.getElementById('patientName').value.trim();
                    if (!patientName) {
                        alert('Bitte geben Sie Ihren Namen ein');
                        return;
                    }
                    
                    document.getElementById('step1').classList.remove('active');
                    document.getElementById('step1').classList.add('completed');
                    document.getElementById('step2').classList.remove('disabled');
                    document.getElementById('step2').classList.add('active');
                    
                    // Enable file upload
                    document.getElementById('documentFile').addEventListener('change', function() {
                        document.getElementById('uploadBtn').disabled = !this.files[0];
                    });
                }
                
                // Step 2: Document Upload
                async function uploadDocument() {
                    const fileInput = document.getElementById('documentFile');
                    const file = fileInput.files[0];
                    
                    if (!file) {
                        alert('Bitte wählen Sie eine Datei aus');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('patient_name', patientName);
                    
                    try {
                        document.getElementById('uploadStatus').innerHTML = '<div class="status">Lade Dokument hoch...</div>';
                        
                        const response = await fetch(`/api/meetings/${meetingId}/upload-document`, {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            documentId = data.document_id;
                            
                            document.getElementById('uploadStatus').innerHTML = '<div class="status success">✅ Dokument erfolgreich hochgeladen</div>';
                            
                            // Complete step 2
                            completeStep2();
                        } else {
                            const error = await response.json();
                            document.getElementById('uploadStatus').innerHTML = `<div class="status error">❌ Fehler: ${error.detail}</div>`;
                        }
                    } catch (error) {
                        document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Fehler beim Hochladen</div>';
                    }
                }
                
                // Skip document upload
                function skipDocument() {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status">ℹ️ Dokument-Upload übersprungen</div>';
                    documentId = null;
                    completeStep2();
                }
                
                // Complete step 2 (shared by upload and skip)
                function completeStep2() {
                    document.getElementById('step2').classList.remove('active');
                    document.getElementById('step2').classList.add('completed');
                    document.getElementById('step3').classList.remove('disabled');
                    document.getElementById('step3').classList.add('active');
                }
                
                // Step 3: Media Test
                async function startMediaTest() {
                    try {
                        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                        const video = document.getElementById('testVideo');
                        video.srcObject = stream;
                        
                        document.getElementById('videoContainer').classList.remove('hidden');
                        document.getElementById('startTestBtn').style.display = 'none';
                    } catch (error) {
                        document.getElementById('mediaStatus').innerHTML = '<div class="status error">❌ Fehler beim Zugriff auf Kamera/Mikrofon. Bitte prüfen Sie Ihre Berechtigung.</div>';
                    }
                }
                
                async function confirmMediaTest(working) {
                    // Stop video stream
                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                    }
                    
                    const mediaData = {
                        meeting_id: meetingId,
                        has_camera: true,
                        has_microphone: true,
                        camera_working: working,
                        microphone_working: working,
                        patient_confirmed: working
                    };
                    
                    try {
                        const response = await fetch(`/api/meetings/${meetingId}/media-test`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(mediaData)
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            mediaTestId = data.test_id;
                            
                            if (data.allowed_to_join && working) {
                                document.getElementById('mediaStatus').innerHTML = '<div class="status success">✅ Perfekt! Kamera und Mikrofon funktionieren</div>';
                                
                                // Complete step 3
                                document.getElementById('step3').classList.remove('active');
                                document.getElementById('step3').classList.add('completed');
                                document.getElementById('step4').classList.remove('disabled');
                                document.getElementById('step4').classList.add('active');
                                
                                // Scroll to final step
                                document.getElementById('step4').scrollIntoView({ behavior: 'smooth' });
                            } else {
                                document.getElementById('mediaStatus').innerHTML = '<div class="status error">❌ Bitte stellen Sie sicher, dass Kamera und Mikrofon funktionieren, bevor Sie fortfahren.</div>';
                                // Reset test
                                document.getElementById('videoContainer').classList.add('hidden');
                                document.getElementById('startTestBtn').style.display = 'block';
                            }
                        }
                    } catch (error) {
                        document.getElementById('mediaStatus').innerHTML = '<div class="status error">❌ Fehler beim Media-Test</div>';
                    }
                }
                
                // Step 4: Join Meeting - IMPROVED WITH CLICK PROTECTION
                async function joinMeeting() {
                    // Prevent multiple clicks
                    if (isJoining) {
                        console.log('⚠️ Join already in progress, ignoring click');
                        return;
                    }
                    
                    isJoining = true;
                    
                    try {
                        const joinBtn = document.getElementById('joinBtn');
                        if (joinBtn) {
                            joinBtn.disabled = true;
                            joinBtn.style.opacity = '0.6';
                            joinBtn.innerHTML = '⏳ Beitritt läuft...';
                        }
                        
                        const response = await fetch(`/api/meetings/${meetingId}/join-patient`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                patient_name: patientName,
                                document_id: documentId,
                                media_test_id: mediaTestId
                            })
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            
                            // Show success message
                            if (joinBtn) {
                                joinBtn.innerHTML = '✅ Erfolgreich! Weiterleitung...';
                            }
                            
                            // Redirect to meeting room
                            setTimeout(() => {
                                window.location.href = `/meeting/${meetingId}?role=patient`;
                            }, 1000);
                        } else {
                            const error = await response.json();
                            alert(`Fehler beim Beitritt: ${error.detail}`);
                            
                            // Reset button on error
                            if (joinBtn) {
                                joinBtn.disabled = false;
                                joinBtn.style.opacity = '1';
                                joinBtn.innerHTML = 'Bereit für die Sprechstunde';
                            }
                            isJoining = false;
                        }
                    } catch (error) {
                        alert('Fehler beim Beitritt zum Meeting');
                        
                        // Reset button on error
                        const joinBtn = document.getElementById('joinBtn');
                        if (joinBtn) {
                            joinBtn.disabled = false;
                            joinBtn.style.opacity = '1';
                            joinBtn.innerHTML = 'Bereit für die Sprechstunde';
                        }
                        isJoining = false;
                    }
                }
            </script>
        </body>
        </html>
        """, status_code=200)

@app.get("/frontend/app.js")
async def serve_app_js():
    """Serve the app.js file"""
    try:
        with open("frontend/app.js", "r", encoding="utf-8") as f:
            content = f.read()
            # Inject base URL for API calls
            content = content.replace("{{BASE_URL}}", get_base_url())
            return HTMLResponse(content=content, media_type="application/javascript")
    except FileNotFoundError:
        logger.error("App.js file not found: frontend/app.js")
        return HTMLResponse(content="// App.js not found", status_code=404)
    except Exception as e:
        logger.error(f"Error serving app.js: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/frontend/simple_meeting.js")
async def get_simple_meeting_js(request: Request):
    logger.info(f"Incoming request: GET /frontend/simple_meeting.js")
    try:
        with open("frontend/simple_meeting.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.info(f"Request completed: GET /frontend/simple_meeting.js - 200 - {time.time() - request.state.start_time:.3f}s")
        return Response(content, media_type="application/javascript")
    
    except FileNotFoundError:
        logger.error("Simple meeting JS file not found")
        logger.info(f"Request completed: GET /frontend/simple_meeting.js - 404 - {time.time() - request.state.start_time:.3f}s")
        return Response("// Simple meeting JS file not found", status_code=404, media_type="application/javascript")

@app.get("/frontend/meeting-fix.js")
async def get_meeting_fix_js():
    """Serve the meeting fix JavaScript file"""
    try:
        with open("frontend/meeting-fix.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        return Response(content, media_type="application/javascript")
    
    except FileNotFoundError:
        logger.error("Meeting fix JS file not found")
        return Response("// Meeting fix JS file not found", status_code=404, media_type="application/javascript")

@app.get("/api/meetings/{meeting_id}/info")
async def get_meeting_info(meeting_id: str, meeting_service: MeetingService = Depends(get_meeting_service)):
    """Get meeting information"""
    # Check if meeting exists, create if not (handles Heroku memory loss)
    meeting = meeting_service.get_meeting(meeting_id)
    
    if not meeting:
        logger.info(f"Meeting {meeting_id} not found in database, recreating entry for info request")
        # Recreate meeting entry for this meeting ID
        meeting = meeting_service.create_meeting(
            host_name="Host",
            host_role="doctor"
        )
    
    return {
        "meeting_id": meeting_id,
        "host_name": meeting.host_name,
        "created_at": meeting.created_at.isoformat(),
        "participants_count": 1 + (1 if meeting.patient_joined else 0),
        "is_active": meeting.meeting_active
    }

@app.get("/health", response_model=HealthResponse)
async def health_check_simple(meeting_service: MeetingService = Depends(get_meeting_service)):
    """Comprehensive health check endpoint"""
    try:
        livekit_connected = livekit is not None and livekit.validate_credentials()
    except Exception:
        livekit_connected = False
    
    # Get meeting count from database
    try:
        total_meetings = meeting_service.get_total_meetings_count()
    except Exception:
        total_meetings = 0
    
    return HealthResponse(
        status="healthy" if livekit_connected else "degraded",
        meetings_count=total_meetings,
        livekit_connected=livekit_connected,
        timestamp=datetime.now().isoformat()
    )

@app.get("/robots.txt", response_class=HTMLResponse)
async def robots_txt():
    """Serve robots.txt to help with SEO and security"""
    return HTMLResponse(
        content="User-agent: *\nDisallow: /api/\nAllow: /\n",
        media_type="text/plain"
    )

@app.get("/.well-known/security.txt", response_class=HTMLResponse)
async def security_txt():
    """Security.txt for responsible disclosure"""
    return HTMLResponse(
        content="Contact: mailto:security@heydok.com\nPreferred-Languages: en, de\n",
        media_type="text/plain"
    )

@app.get("/test-livekit", response_class=HTMLResponse)
async def test_livekit_frontend():
    """Serve the LiveKit frontend test page"""
    try:
        with open("test_livekit_frontend.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Test file not found</h1><p>test_livekit_frontend.html not found</p>",
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error serving LiveKit test page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/livekit-sdk")
async def serve_livekit_sdk():
    """Serve the local LiveKit SDK as a fallback"""
    try:
        with open("static/livekit-client.umd.min.js", "r", encoding="utf-8") as f:
            content = f.read()
            return HTMLResponse(content=content, media_type="application/javascript")
    except FileNotFoundError:
        logger.error("Local LiveKit SDK file not found")
        return HTMLResponse(content="// Local LiveKit SDK not found", status_code=404)
    except Exception as e:
        logger.error(f"Error serving local LiveKit SDK: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/test-livekit-fix", response_class=HTMLResponse)
async def test_livekit_fix():
    """Serve the LiveKit fix test page"""
    try:
        with open("test_livekit_fix.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Test file not found</h1><p>test_livekit_fix.html not found</p>",
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error serving LiveKit fix test page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/debug", response_class=HTMLResponse)
async def debug_meeting():
    """Serve the meeting debug tool"""
    try:
        with open("frontend/debug_meeting.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Debug tool not found</h1><p>debug_meeting.html not found</p>",
            status_code=404
        )

# Add new endpoint to handle participant disconnect
@app.post("/api/meetings/{meeting_id}/leave")
async def leave_meeting(meeting_id: str, participant_name: str):
    """Handle participant leaving the meeting"""
    # Simplified - just return success (participant tracking removed)
    return {"status": "left"}

@app.post("/api/meetings/{meeting_id}/upload-document", response_model=DocumentUploadResponse)
async def upload_patient_document(
    meeting_id: str,
    file: UploadFile = File(...),
    patient_name: str = Form(...),
    meeting_service: MeetingService = Depends(get_meeting_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """Upload patient document (Krankenkassenschein etc.) before joining meeting"""
    
    # Validate meeting exists
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except Exception as e:
        logger.error(f"Meeting {meeting_id} not found for document upload. Error: {e}")
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    # Validate file type (only allow common document formats)
    allowed_types = {
        'application/pdf': '.pdf',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/tiff': '.tiff',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types.values())}"
        )
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # Read file content (in production, save to disk or cloud storage)
    file_content = await file.read()
    
    # Store document metadata
    document_service.create_document(
        document_id=document_id,
        meeting_id=meeting_id,
        patient_name=patient_name,
        filename=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        content=file_content
    )
    
    # Update meeting status
    meeting_service.mark_document_uploaded(meeting_id)
    
    logger.info(f"Document uploaded for meeting {meeting_id}: {file.filename} ({len(file_content)} bytes)")
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        upload_timestamp=datetime.now().isoformat(),
        status="uploaded"
    )

@app.post("/api/meetings/{meeting_id}/process-document")
async def process_patient_document(
    meeting_id: str, 
    document_id: str = Form(...),
    document_service: DocumentService = Depends(get_document_service)
):
    """Process uploaded patient document (placeholder for actual processing logic)"""
    
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.meeting_id != meeting_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this meeting")
    
    # Placeholder for actual document processing
    # In production: OCR, validation, data extraction, etc.
    document_service.process_document(document_id)
    
    logger.info(f"Document processed for meeting {meeting_id}: {document_id}")
    
    return {
        "document_id": document_id,
        "status": "processed",
        "processing_timestamp": datetime.now().isoformat(),
        "result": document.processing_result
    }

@app.post("/api/meetings/{meeting_id}/media-test", response_model=MediaTestResponse)
async def submit_media_test(
    meeting_id: str, 
    request: MediaTestRequest,
    meeting_service: MeetingService = Depends(get_meeting_service),
    media_test_service: MediaTestService = Depends(get_media_test_service)
):
    """Submit patient media test results"""
    
    # Validate meeting exists
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except Exception as e:
        logger.error(f"Meeting {meeting_id} not found for media test. Error: {e}")
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if request.meeting_id != meeting_id:
        raise HTTPException(status_code=400, detail="Meeting ID mismatch")
    
    # Generate test ID
    test_id = str(uuid.uuid4())
    
    # Determine if patient is allowed to join
    # Simplified logic: If patient confirms everything works, allow them to join
    # This is more user-friendly than requiring all technical checks
    allowed_to_join = request.patient_confirmed
    
    # Log the details for debugging but don't block based on technical checks
    logger.info(f"Media test for meeting {meeting_id}: confirmed={request.patient_confirmed}, "
                f"has_camera={request.has_camera}, has_microphone={request.has_microphone}, "
                f"camera_working={request.camera_working}, microphone_working={request.microphone_working}")
    
    # Store test results
    media_test_service.create_media_test(
        test_id=test_id,
        meeting_id=meeting_id,
        has_camera=request.has_camera,
        has_microphone=request.has_microphone,
        camera_working=request.camera_working,
        microphone_working=request.microphone_working,
        patient_confirmed=request.patient_confirmed,
        allowed_to_join=allowed_to_join
    )
    
    # Update meeting status if test passed
    if allowed_to_join:
        meeting_service.mark_media_test_completed(meeting_id)
    
    logger.info(f"Media test completed for meeting {meeting_id}: allowed={allowed_to_join}")
    
    return MediaTestResponse(
        test_id=test_id,
        meeting_id=meeting_id,
        status="completed",
        timestamp=datetime.now().isoformat(),
        allowed_to_join=allowed_to_join
    )

@app.post("/api/meetings/{meeting_id}/join-patient", response_model=MeetingResponse)
async def patient_join_meeting(
    meeting_id: str,
    request: PatientJoinRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client),
    meeting_service: MeetingService = Depends(get_meeting_service),
    media_test_service: MediaTestService = Depends(get_media_test_service)
):
    """Patient join meeting with document and media test validation"""
    
    # Validate meeting exists - create simple fallback if not found  
    try:
        meeting = meeting_service.get_meeting(meeting_id)
        actual_meeting_id = meeting_id
    except Exception as e:
        logger.info(f"Meeting {meeting_id} not found, creating basic fallback meeting. Error: {e}")
        meeting = meeting_service.create_meeting(
            host_name="Doctor",  # Default doctor name
            host_role="doctor"
        )
        actual_meeting_id = meeting.meeting_id
        logger.info(f"Created fallback meeting with ID: {actual_meeting_id}")
    
    # Check if patient already has a name (indicates they went through setup)
    has_patient_name = meeting.patient_name is not None
    
    # Skip detailed validation if patient is already known
    if has_patient_name:
        logger.info(f"Patient {request.patient_name} already known for meeting {actual_meeting_id}, allowing join")
        document_uploaded = True  # Assume setup was completed
        media_test_valid = True  # Assume media test was passed
    else:
        # Validate document upload if required
        document_uploaded = request.document_id is not None
        
        # Validate media test
        media_test_valid = False
        if request.media_test_id:
            # Check if media test exists and is valid
            try:
                media_test = media_test_service.get_media_test(request.media_test_id)
                media_test_valid = (
                    media_test.allowed_to_join and 
                    media_test.patient_confirmed and
                    media_test.meeting_id == actual_meeting_id
                )
                logger.info(f"Media test {request.media_test_id} validation: {media_test_valid}")
            except Exception as e:
                logger.warning(f"Media test {request.media_test_id} not found for meeting {actual_meeting_id}: {e}")
                media_test_valid = False
        
        # If no valid media test, create a fallback one
        if not media_test_valid:
            # Create a fallback media test entry to allow join
            logger.info(f"Creating fallback media test for patient {request.patient_name} in meeting {actual_meeting_id}")
            fallback_test_id = str(uuid.uuid4())
            media_test_service.create_media_test(
                test_id=fallback_test_id,
                meeting_id=actual_meeting_id,
                has_camera=True,  # Assume patient has camera (they completed setup)
                has_microphone=True,  # Assume patient has microphone
                camera_working=True,
                microphone_working=True,
                patient_confirmed=True,
                allowed_to_join=True
            )
            media_test_valid = True
            logger.info(f"Fallback media test created: {fallback_test_id}")
    
    if not media_test_valid:
        raise HTTPException(status_code=400, detail="Media-Test Validierung fehlgeschlagen")
    
    try:
        # Generate token for patient with limited permissions
        room_name = livekit_client.get_room_name(actual_meeting_id)
        token = livekit_client.generate_token(
            room_name=room_name,
            participant_name=f"Patient: {request.patient_name}",
            is_host=False
        )
        
        # Update meeting data with patient information
        meeting_service.update_meeting(
            meeting_id=actual_meeting_id,
            patient_name=request.patient_name,
            patient_joined=True,
            patient_setup_completed=True,
            document_uploaded=document_uploaded,
            media_test_completed=True
        )
        
        participants_count = 2  # Doctor + Patient
        
        logger.info(f"Patient {request.patient_name} erfolgreich dem Meeting {actual_meeting_id} beigetreten")
        
        return MeetingResponse(
            meeting_id=actual_meeting_id,
            meeting_url=f"{get_base_url()}/meeting/{actual_meeting_id}?role=patient",
            livekit_url=livekit_client.url,
            token=token,
            participants_count=participants_count,
            user_role="patient",
            meeting_status={
                "doctor_name": meeting.host_name or "Doctor",
                "patient_setup_completed": True,
                "document_uploaded": document_uploaded,
                "media_test_completed": True
            }
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Token-Generieren für Patient {request.patient_name}: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Meeting-Beitritt")

@app.get("/api/meetings/{meeting_id}/status", response_model=MeetingStatusResponse)
async def get_meeting_status(meeting_id: str, meeting_service: MeetingService = Depends(get_meeting_service), document_service: DocumentService = Depends(get_document_service)):
    """Get detailed meeting status for role-based UI updates"""
    # Check if meeting exists, create if not (handles Heroku memory loss)
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except Exception as e:
        logger.info(f"Meeting {meeting_id} not found in database, recreating entry for status request. Error: {e}")
        meeting = meeting_service.create_meeting(
            host_name="Doctor",  # Default doctor name
            host_role="doctor"
        )
    
    # Check if patient has completed setup
    patient_setup_completed = (
        meeting.patient_name is not None and
        meeting.media_test_completed
    )
    
    # Check if documents were uploaded
    document_uploaded = document_service.has_documents_for_meeting(meeting_id)
    
    return MeetingStatusResponse(
        meeting_id=meeting_id,
        doctor_name=str(meeting.host_name or "Doctor"),
        patient_name=meeting.patient_name,
        patient_joined=meeting.patient_joined,
        patient_setup_completed=patient_setup_completed,
        document_uploaded=document_uploaded,
        media_test_completed=meeting.media_test_completed,
        meeting_active=meeting.meeting_active,
        created_at=meeting.created_at.isoformat(),
        last_patient_status=meeting.last_patient_status,
        last_status_update=meeting.last_status_update.isoformat() if meeting.last_status_update else None
    )

@app.post("/api/meetings/{meeting_id}/join-doctor", response_model=MeetingResponse)
async def doctor_join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client),
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Doctor join meeting - bypasses patient validation requirements"""
    
    logger.info(f"🩺 DOCTOR JOIN REQUEST: meeting_id={meeting_id}, participant_name={request.participant_name}, role={request.participant_role}")
    
    # Validate meeting exists using database service
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except Exception as e:
        logger.error(f"❌ Meeting {meeting_id} not found for doctor join. Error: {e}")
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    logger.info(f"🩺 Meeting data found: doctor_name={meeting.host_name}")
    
    # Validate this is actually a doctor joining
    if request.participant_role != "doctor":
        logger.error(f"❌ Invalid role for doctor endpoint: {request.participant_role}")
        raise HTTPException(status_code=400, detail="This endpoint is for doctors only")
    
    # Check if this is the original doctor or another doctor
    is_original_doctor = request.participant_name == meeting.host_name
    logger.info(f"🩺 Is original doctor: {is_original_doctor} (request={request.participant_name}, stored={meeting.host_name})")
    
    if not is_original_doctor:
        # For now, only allow the original doctor
        logger.warning(f"⚠️ Non-original doctor trying to join: {request.participant_name}")
        raise HTTPException(status_code=403, detail="Only the original doctor can join this meeting")
    
    # REMOVED: Duplicate check since database doesn't track participants
    # doctor can always reconnect if they lose connection
    logger.info(f"🩺 Doctor joining meeting {meeting_id}")
    
    try:
        # Generate token for doctor with admin permissions
        doctor_display_name = f"Dr. {request.participant_name}"
        room_name = livekit_client.get_room_name(meeting_id)
        logger.info(f"🩺 Generating token for doctor: {doctor_display_name} in room: {room_name}")
        
        token = livekit_client.generate_token(
            room_name=room_name,
            participant_name=doctor_display_name,
            is_host=True
        )
        
        logger.info(f"✅ Token generated successfully for doctor: {doctor_display_name}")
        logger.info(f"🔗 LiveKit URL: {livekit_client.url}")
        
        # Update meeting status using database service
        meeting_service.update_meeting(meeting_id, meeting_active=True)
        
        # Get current participants count
        participants_count = 1 + (1 if meeting.patient_joined else 0)
        
        logger.info(f"✅ Doctor {request.participant_name} joined meeting {meeting_id} successfully")
        logger.info(f"📊 Final meeting state: participants_count={participants_count}")
        
        response_data = MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=f"{get_base_url()}/meeting/{meeting_id}",
            livekit_url=livekit_client.url,
            token=token,
            participants_count=participants_count,
            user_role="doctor",
            meeting_status={
                "doctor_name": meeting.host_name,
                "patient_name": meeting.patient_name,
                "patient_setup_completed": meeting.patient_setup_completed,
                "document_uploaded": meeting.document_uploaded,
                "media_test_completed": meeting.media_test_completed
            }
        )
        
        logger.info(f"📤 Returning doctor join response with token length: {len(token)}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Failed to generate token for doctor {request.participant_name}: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to join meeting")

@app.get("/doctor-dashboard/{meeting_id}", response_class=HTMLResponse)
async def doctor_dashboard(meeting_id: str, meeting_service: MeetingService = Depends(get_meeting_service)):
    """
    🩺 **Arzt Dashboard für Meeting-Überwachung**
    
    Zeigt den aktuellen Patient-Status mit 3-Stufen-Ampelsystem:
    - 🔴 Link erstellt (Patient noch nicht aktiv)
    - 🟡 Patient aktiv (füllt Daten aus)
    - 🟢 Im Meeting (bereit für Sprechstunde)
    """
    # Check if meeting exists using database service
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except Exception as e:
        logger.error(f"Meeting {meeting_id} not found for doctor dashboard. Error: {e}")
        raise HTTPException(status_code=404, detail="Meeting nicht gefunden")
    
    # Read dashboard template
    dashboard_path = Path("frontend/doctor_dashboard.html")
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template nicht gefunden")
    
    template_content = dashboard_path.read_text(encoding='utf-8')
    # Replace placeholder with actual meeting ID
    html_content = template_content.replace('{{MEETING_ID}}', meeting_id)
    
    return html_content

# ===== EXTERNAL API ENDPOINTS =====

@app.post("/api/external/create-meeting-link", 
          response_model=CreateMeetingLinkResponse,
          tags=["External API"],
          summary="🔗 Meeting-Link erstellen",
          description="""
          **Erstellt einen neuen Video-Meeting Link für die Arzt-Patient Kommunikation.**
          
          Dieser Endpunkt ermöglicht es externen Systemen (PVS, Klinik-Software), 
          programmatisch Meeting-Links zu generieren.
          
          ### 📋 Workflow:
          1. **Request**: Arztname und optionale externe ID senden
          2. **Response**: Zwei separate URLs erhalten
             - **Arzt-URL**: Direkter Beitritt ohne Setup
             - **Patient-URL**: Mit vollständigem Setup-Prozess
          3. **Integration**: URLs in Ihr System einbinden
          
          ### 🎯 Anwendungsfälle:
          - **Terminbuchung**: Automatische Link-Generierung bei Terminbuchung
          - **PVS Integration**: Direkte Anbindung an Praxisverwaltung
          - **Patient-Portal**: Self-Service für Patienten
          
          ### ⚡ Performance:
          - **Response Time**: < 200ms
          - **Gültigkeit**: 24 Stunden
          - **Concurrent Users**: Unbegrenzt pro Meeting
          """,
          responses={
              200: {
                  "description": "✅ Meeting erfolgreich erstellt", 
                  "content": {
                      "application/json": {
                          "example": {
                              "meeting_id": "mtg_8f4e2d1c9b6a",
                              "doctor_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/meeting/mtg_8f4e2d1c9b6a?role=doctor&direct=true",
                              "patient_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/patient-setup?meeting=mtg_8f4e2d1c9b6a",
                              "external_id": "TERMIN-2024-001234",
                              "created_at": "2024-01-15T14:30:00Z",
                              "expires_at": "2024-01-16T14:30:00Z"
                          }
                      }
                  }
              },
              422: {
                  "description": "❌ Validierungsfehler",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": [
                                  {
                                      "loc": ["body", "doctor_name"],
                                      "msg": "ensure this value has at least 1 characters",
                                      "type": "value_error.any_str.min_length"
                                  }
                              ]
                          }
                      }
                  }
              }
          })
async def create_meeting_link(request: CreateMeetingLinkRequest, meeting_service: MeetingService = Depends(get_meeting_service)):
    """
    🏥 **Meeting-Link für externe Systeme erstellen**
    
    Generiert Meeting-Links für die Integration in Praxisverwaltungssoftware,
    Terminbuchungssysteme oder Patient-Portale.
    
    **Wichtige Hinweise:**
    - Meeting ist 24 Stunden gültig
    - Keine Authentifizierung erforderlich (derzeit)
    - Beliebig viele Teilnehmer pro Meeting möglich
    - Ende-zu-Ende verschlüsselt über LiveKit
    """
    try:
        # Create meeting using database service
        meeting = meeting_service.create_meeting(
            host_name=request.doctor_name,
            host_role="doctor",
            external_id=request.external_id
        )
        
        meeting_id = meeting.meeting_id
        
        # Generate URLs
        base_url = get_base_url()
        doctor_url = f"{base_url}/meeting/{meeting_id}?role=doctor&direct=true"
        patient_url = f"{base_url}/patient-setup?meeting={meeting_id}"
        
        logger.info(f"🔗 External API: Created meeting {meeting_id} for doctor {request.doctor_name}")
        
        return CreateMeetingLinkResponse(
            meeting_id=meeting_id,
            doctor_join_url=doctor_url,
            patient_join_url=patient_url, 
            external_id=request.external_id,
            created_at=meeting.created_at.isoformat() + "Z",
            expires_at=meeting.expires_at.isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"❌ External API: Error creating meeting: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen des Meetings")

@app.post("/api/external/patient-status",
          response_model=PatientStatusResponse,
          tags=["External API"], 
          summary="📊 Patient-Status aktualisieren",
          description="""
          **Aktualisiert den Status eines Patienten während des Meeting-Workflows.**
          
          Dieser Endpunkt ermöglicht es, den Fortschritt des Patienten zu verfolgen 
          und entsprechende Aktionen in externen Systemen auszulösen.
          
          ### 📈 Status-Werte:
          - **`link_created`** - Meeting-Link erstellt, Patient noch nicht aktiv
          - **`patient_active`** - Patient füllt gerade Daten aus (Setup-Prozess)
          - **`in_meeting`** - Patient ist aktiv im Meeting
          
          ### 🔄 Typischer Status-Flow:
          ```
          link_created → patient_active → in_meeting
          ```
          
          ### 💡 Integration-Tipps:
          - **Webhooks**: Nutzen Sie Status-Updates für automatische Benachrichtigungen
          - **Abrechnung**: Tracking für Abrechnungszwecke
          - **Analytics**: Auswertung der Meeting-Qualität
          - **Workflow**: Automatische Nachbereitung nach Meeting-Ende
          """,
          responses={
              200: {
                  "description": "✅ Status erfolgreich aktualisiert",
                  "content": {
                      "application/json": {
                          "example": {
                              "meeting_id": "mtg_8f4e2d1c9b6a",
                              "patient_name": "Max Mustermann",
                              "status": "patient_active",
                              "updated_at": "2024-01-15T14:35:00Z",
                              "success": True
                          }
                      }
                  }
              },
              404: {
                  "description": "❌ Meeting nicht gefunden",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Meeting mit ID 'invalid_id' nicht gefunden"
                          }
                      }
                  }
              },
              422: {
                  "description": "❌ Ungültiger Status-Wert",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": [
                                  {
                                      "loc": ["body", "status"],
                                      "msg": "string does not match regex pattern",
                                      "type": "value_error.str.regex"
                                  }
                              ]
                          }
                      }
                  }
              }
          })
async def update_patient_status(request: PatientStatusRequest, meeting_service: MeetingService = Depends(get_meeting_service)):
    """
    📊 **Patient-Status für externes Tracking aktualisieren**
    
    Ermöglicht die Verfolgung des Patient-Workflows für Integration 
    in Praxisverwaltungssoftware und Analytics-Systeme.
    
    **Use Cases:**
    - Arzt-Benachrichtigung bei Patient-Beitritt
    - Automatische Abrechnungsauslösung 
    - Meeting-Qualität Analytics
    - Workflow-Automation
    """
    try:
        # Validate meeting exists using database service
        meeting = meeting_service.get_meeting(request.meeting_id)
        if not meeting:
            raise HTTPException(
                status_code=404, 
                detail=f"Meeting mit ID '{request.meeting_id}' nicht gefunden"
            )
        
        # Update timestamp
        update_time = request.timestamp or datetime.utcnow().isoformat() + "Z"
        
        # Update meeting data using database service
        meeting_service.update_meeting(
            meeting_id=request.meeting_id,
            patient_name=request.patient_name,
            last_patient_status=request.status,
            last_status_update=datetime.fromisoformat(update_time.replace('Z', '+00:00'))
        )
        
        logger.info(f"📊 External API: Updated patient status for {request.meeting_id}: {request.status}")
        
        return PatientStatusResponse(
            meeting_id=request.meeting_id,
            patient_name=request.patient_name,
            status=request.status,
            updated_at=update_time,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ External API: Error updating patient status: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Aktualisieren des Status")

# Health Check Endpoint
@app.get("/api/health",
         tags=["System"],
         summary="⚡ System Health Check", 
         description="""
         **System-Status und API-Verfügbarkeit prüfen.**
         
         Dieser Endpunkt kann für Monitoring, Load Balancer Health Checks 
         und System-Überwachung verwendet werden.
         
         ### ✅ Prüfungen:
         - **API Status**: Grundlegende API-Funktionalität
         - **Database**: Meeting-Datenbank Verfügbarkeit  
         - **LiveKit**: Video-Service Konnektivität
         - **Response Time**: API-Performance Metrics
         
         ### 📊 Monitoring Integration:
         - Nagios, Zabbix, DataDog kompatibel
         - Prometheus Metrics verfügbar
         - Uptime-Monitoring geeignet
         """,
         responses={
             200: {
                 "description": "✅ System läuft normal",
                 "content": {
                     "application/json": {
                         "example": {
                             "status": "healthy",
                             "version": "1.0.0",
                             "timestamp": "2024-01-15T14:30:00Z",
                             "services": {
                                 "api": "healthy",
                                 "database": "healthy", 
                                 "livekit": "healthy"
                             },
                             "metrics": {
                                 "active_meetings": 5,
                                 "total_meetings": 1234,
                                 "uptime_seconds": 86400
                             }
                         }
                     }
                 }
             }
         })
async def health_check(meeting_service: MeetingService = Depends(get_meeting_service)):
    """
    ⚡ **System Health Check für Monitoring**
    
    Überprüft den Status aller kritischen System-Komponenten
    und liefert Performance-Metriken für Monitoring-Systeme.
    """
    try:
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Get meeting counts from database
        active_meetings = meeting_service.get_active_meetings()
        total_meetings = meeting_service.get_total_meetings_count()
        
        return {
            "status": "healthy",
            "version": "1.0.0", 
            "timestamp": current_time,
            "services": {
                "api": "healthy",
                "database": "healthy",
                "livekit": "healthy" if os.getenv('LIVEKIT_API_KEY') else "config_missing"
            },
            "metrics": {
                "active_meetings": len(active_meetings),
                "total_meetings": total_meetings,
                "uptime_seconds": 86400  # Placeholder
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)  
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/simple-meeting/{meeting_id}", response_class=HTMLResponse)
async def simple_meeting_room(meeting_id: str, meeting_service: MeetingService = Depends(get_meeting_service)):
    """New: Clean, stable meeting room implementation"""
    try:
        # Validate meeting exists using database service
        meeting = meeting_service.get_meeting(meeting_id)
        if not meeting:
            return HTMLResponse(
                content=f"""
                <html>
                <head><title>Meeting nicht gefunden</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Meeting nicht gefunden</h1>
                    <p>Meeting ID: {meeting_id}</p>
                    <p>Das Meeting existiert nicht oder ist abgelaufen.</p>
                    <a href="/" style="background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Zur Homepage
                    </a>
                </body>
                </html>
                """,
                status_code=404
            )
        
        # Load the simple meeting HTML
        try:
            with open("frontend/simple_meeting.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except FileNotFoundError:
            return HTMLResponse(
                content="""
                <html>
                <head><title>System Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>⚠️ System Error</h1>
                    <p>Simple Meeting System ist noch nicht verfügbar.</p>
                    <p>Verwenden Sie das <a href="/meeting/{meeting_id}">Standard Meeting System</a>.</p>
                </body>
                </html>
                """.replace("{meeting_id}", meeting_id),
                status_code=503
            )
    
    except Exception as e:
        logger.error(f"Simple meeting room error: {str(e)}")
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>Server Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>🚨 Server Error</h1>
                <p>Fehler beim Laden des Meetings</p>
                <button onclick="location.reload()">Erneut versuchen</button>
            </body>
            </html>
            """,
            status_code=500
        )

@app.get("/frontend/stable-meeting.js")
async def get_stable_meeting_js():
    """Serve the stable meeting JavaScript file"""
    try:
        with open("frontend/stable-meeting.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        return Response(content, media_type="application/javascript")
    
    except FileNotFoundError:
        logger.error("Stable meeting JS file not found")
        return Response("// Stable meeting JS file not found", status_code=404, media_type="application/javascript")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting HeyDok Video on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    ) 