import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid
import mimetypes

from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
    title="HeyDok Video - Simple Video Meetings",
    description="A minimal video meeting platform powered by LiveKit",
    version="1.0.0"
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
            return JSONResponse(
                status_code=301,
                headers={"Location": str(url)}
            )
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

# In-memory storage for meetings (use Redis/Database in production)
meetings: Dict[str, dict] = {}

# Track active participants to prevent duplicates
active_participants: Dict[str, set] = {}

# Storage for patient documents and media tests
patient_documents: Dict[str, dict] = {}
media_tests: Dict[str, dict] = {}

# Cleanup old meetings periodically (simple in-memory cleanup)
def cleanup_old_meetings():
    """Remove meetings older than 24 hours and related documents/tests"""
    now = datetime.now()
    expired_meetings = []
    
    for meeting_id, meeting_data in meetings.items():
        created_at = datetime.fromisoformat(meeting_data["created_at"])
        if now - created_at > timedelta(hours=24):
            expired_meetings.append(meeting_id)
    
    for meeting_id in expired_meetings:
        del meetings[meeting_id]
        
        # Clean up related documents
        expired_docs = [doc_id for doc_id, doc_data in patient_documents.items() 
                       if doc_data["meeting_id"] == meeting_id]
        for doc_id in expired_docs:
            del patient_documents[doc_id]
        
        # Clean up related media tests
        expired_tests = [test_id for test_id, test_data in media_tests.items() 
                        if test_data["meeting_id"] == meeting_id]
        for test_id in expired_tests:
            del media_tests[test_id]
        
        # Clean up active participants
        if meeting_id in active_participants:
            del active_participants[meeting_id]
        
        logger.info(f"Cleaned up expired meeting: {meeting_id} (with {len(expired_docs)} docs and {len(expired_tests)} tests)")
    
    logger.info(f"Active meetings: {len(meetings)}, Documents: {len(patient_documents)}, Media tests: {len(media_tests)}")

# Request/Response models
class CreateMeetingRequest(BaseModel):
    host_name: str = Field(default="Host", min_length=1, max_length=50)
    host_role: str = Field(default="doctor", regex="^(doctor|patient)$")  # New: explicit role

class JoinMeetingRequest(BaseModel):
    participant_name: str = Field(min_length=1, max_length=50)
    participant_role: str = Field(default="patient", regex="^(doctor|patient)$")  # New: explicit role

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
    doctor_joined: bool
    patient_name: Optional[str] = None
    patient_joined: bool
    patient_setup_completed: bool
    document_uploaded: bool
    media_test_completed: bool
    meeting_active: bool
    created_at: str

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
                    <p><strong>Patient-Link:</strong></p>
                    <input type="text" id="patientLink" readonly onclick="this.select()">
                    <button onclick="copyPatientLink()">Link kopieren</button>
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
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Create a new meeting - typically called by doctors"""
    cleanup_old_meetings()
    
    meeting_id = generate_meeting_id()
    room_name = livekit_client.get_room_name(meeting_id)
    
    # Generate doctor token with admin permissions
    token = livekit_client.generate_token(
        room_name=room_name,
        participant_name=f"Dr. {request.host_name}",
        is_host=True,
        metadata={"role": "doctor", "permissions": ["admin", "record", "moderate"]}
    )
    
    # Store meeting with role-based structure
    meetings[meeting_id] = {
        "id": meeting_id,
        "room_name": room_name,
        "created_at": datetime.now().isoformat(),
        "doctor_name": request.host_name,
        "doctor_role": request.host_role,
        "doctor_joined": False,
        "patient_name": None,
        "patient_joined": False,
        "patient_setup_completed": False,
        "document_uploaded": False,
        "media_test_completed": False,
        "meeting_active": True,
        "participants": [{
            "name": request.host_name, 
            "role": "doctor", 
            "joined_at": datetime.now().isoformat(),
            "token_generated": True
        }],
        "max_participants": 2  # Doctor + Patient only
    }
    
    # Initialize participant tracking
    active_participants[meeting_id] = {f"doctor_{request.host_name}"}
    
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
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Join an existing meeting with duplicate prevention"""
    # Check if meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting = meetings[meeting_id]
    
    # Check participant limit
    if len(meeting["participants"]) >= meeting.get("max_participants", 10):
        raise HTTPException(status_code=429, detail="Meeting is full")
    
    # IMPORTANT: Prevent duplicate participants
    if meeting_id not in active_participants:
        active_participants[meeting_id] = set()
    
    participant_name = request.participant_name.strip()
    
    # Check if participant already exists in this meeting
    if participant_name in active_participants[meeting_id]:
        logger.warning(f"Participant {participant_name} already exists in meeting {meeting_id}")
        # Return existing token or generate new one for reconnection
        pass  # Allow reconnection with new token
    else:
        # Add to active participants
        active_participants[meeting_id].add(participant_name)
    
    room_name = meeting["room_name"]
    
    # Generate participant token
    token = livekit_client.generate_token(
        room_name=room_name,
        participant_name=participant_name,
        is_host=False
    )
    
    # Add participant to meeting if not already present
    existing_participant = next((p for p in meeting["participants"] if p["name"] == participant_name), None)
    if not existing_participant:
        meeting["participants"].append({
            "name": participant_name,
            "role": "participant",
            "joined_at": datetime.now().isoformat()
        })
    else:
        # Update join time for reconnection
        existing_participant["joined_at"] = datetime.now().isoformat()
    
    base_url = get_base_url()
    
    return MeetingResponse(
        meeting_id=meeting_id,
        meeting_url=f"{base_url}/meeting/{meeting_id}",
        livekit_url=livekit_client.url,
        token=token,
        participants_count=len(meeting["participants"]),
        user_role=request.participant_role,
        meeting_status={}
    )

@app.get("/meeting/{meeting_id}", response_class=HTMLResponse)
async def meeting_room(meeting_id: str, role: Optional[str] = None):
    """Serve the meeting room page with role-based interface"""
    # Validate meeting exists
    if meeting_id not in meetings:
        return HTMLResponse(
            content="<h1>Meeting not found</h1><p>The meeting you're looking for doesn't exist or has expired.</p>",
            status_code=404
        )
    
    meeting_data = meetings[meeting_id]
    
    # Determine user role (default to doctor if not specified)
    user_role = role or "doctor"
    
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
        
        # Replace placeholders with actual values
        html_content = html_content.replace("{{MEETING_ID}}", meeting_id)
        html_content = html_content.replace("{{USER_ROLE}}", user_role)
        html_content = html_content.replace("{{DOCTOR_NAME}}", meeting_data["doctor_name"])
        html_content = html_content.replace("{{PATIENT_NAME}}", meeting_data.get("patient_name", ""))
        
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
        logger.error("patient_setup.html not found")
        return HTMLResponse(
            content="<h1>Error</h1><p>Patient setup page not found. Please check your installation.</p>",
            status_code=500
        )

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

@app.get("/api/meetings/{meeting_id}/info")
async def get_meeting_info(meeting_id: str):
    """Get meeting information"""
    # Check if meeting exists, create if not (handles Heroku memory loss)
    if meeting_id not in meetings:
        logger.info(f"Meeting {meeting_id} not found in memory, recreating entry for info request")
        # Recreate meeting entry for this meeting ID
        meetings[meeting_id] = {
            "id": meeting_id,
            "room_name": f"meeting-{meeting_id}",
            "created_at": datetime.now().isoformat(),
            "host_name": "Host",
            "participants": [],
            "is_active": True
        }
    
    meeting = meetings[meeting_id]
    return {
        "meeting_id": meeting_id,
        "host_name": meeting["host_name"],
        "created_at": meeting["created_at"],
        "participants_count": len(meeting["participants"]),
        "is_active": meeting.get("is_active", True)
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        livekit_connected = livekit is not None and livekit.validate_credentials()
    except Exception:
        livekit_connected = False
    
    return HealthResponse(
        status="healthy" if livekit_connected else "degraded",
        meetings_count=len(meetings),
        livekit_connected=livekit_connected,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/health")
async def api_health_check():
    """Simple API health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
    if meeting_id in active_participants:
        active_participants[meeting_id].discard(participant_name)
        
        # Clean up empty meetings
        if not active_participants[meeting_id]:
            active_participants.pop(meeting_id, None)
            meetings.pop(meeting_id, None)
            logger.info(f"Cleaned up empty meeting: {meeting_id}")
    
    return {"status": "left"}

@app.post("/api/meetings/{meeting_id}/upload-document", response_model=DocumentUploadResponse)
async def upload_patient_document(
    meeting_id: str,
    file: UploadFile = File(...),
    patient_name: str = Form(...)
):
    """Upload patient document (Krankenkassenschein etc.) before joining meeting"""
    
    # Validate meeting exists
    if meeting_id not in meetings:
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
    patient_documents[document_id] = {
        "document_id": document_id,
        "meeting_id": meeting_id,
        "patient_name": patient_name,
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": len(file_content),
        "upload_timestamp": datetime.now().isoformat(),
        "content": file_content,  # In production: store file path instead
        "processed": False
    }
    
    # Update meeting status
    if meeting_id in meetings:
        meetings[meeting_id]["document_uploaded"] = True
    
    logger.info(f"Document uploaded for meeting {meeting_id}: {file.filename} ({len(file_content)} bytes)")
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        upload_timestamp=datetime.now().isoformat(),
        status="uploaded"
    )

@app.post("/api/meetings/{meeting_id}/process-document")
async def process_patient_document(meeting_id: str, document_id: str = Form(...)):
    """Process uploaded patient document (placeholder for actual processing logic)"""
    
    if document_id not in patient_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = patient_documents[document_id]
    
    if document["meeting_id"] != meeting_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this meeting")
    
    # Placeholder for actual document processing
    # In production: OCR, validation, data extraction, etc.
    document["processed"] = True
    document["processing_timestamp"] = datetime.now().isoformat()
    document["processing_result"] = {
        "status": "success",
        "extracted_data": {
            "patient_name": document["patient_name"],
            "document_type": "insurance_card",  # Example
            "validation_status": "valid"
        }
    }
    
    logger.info(f"Document processed for meeting {meeting_id}: {document_id}")
    
    return {
        "document_id": document_id,
        "status": "processed",
        "processing_timestamp": datetime.now().isoformat(),
        "result": document["processing_result"]
    }

@app.post("/api/meetings/{meeting_id}/media-test", response_model=MediaTestResponse)
async def submit_media_test(meeting_id: str, request: MediaTestRequest):
    """Submit patient media test results"""
    
    # Validate meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if request.meeting_id != meeting_id:
        raise HTTPException(status_code=400, detail="Meeting ID mismatch")
    
    # Generate test ID
    test_id = str(uuid.uuid4())
    
    # Determine if patient is allowed to join
    allowed_to_join = (
        request.has_camera and 
        request.has_microphone and 
        request.camera_working and 
        request.microphone_working and 
        request.patient_confirmed
    )
    
    # Store test results
    media_tests[test_id] = {
        "test_id": test_id,
        "meeting_id": meeting_id,
        "has_camera": request.has_camera,
        "has_microphone": request.has_microphone,
        "camera_working": request.camera_working,
        "microphone_working": request.microphone_working,
        "patient_confirmed": request.patient_confirmed,
        "allowed_to_join": allowed_to_join,
        "timestamp": datetime.now().isoformat()
    }
    
    # Update meeting status if test passed
    if allowed_to_join and meeting_id in meetings:
        meetings[meeting_id]["media_test_completed"] = True
    
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
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Patient join meeting with document and media test validation"""
    
    # Validate meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting_data = meetings[meeting_id]
    
    # Check if patient already joined
    if meeting_data.get("patient_joined", False):
        raise HTTPException(status_code=409, detail="Patient already joined this meeting")
    
    # Validate document upload (optional but recommended)
    document_uploaded = False
    if request.document_id:
        if request.document_id not in patient_documents:
            raise HTTPException(status_code=400, detail="Document not found")
        document = patient_documents[request.document_id]
        if not document.get("processed", False):
            raise HTTPException(status_code=400, detail="Document not yet processed")
        document_uploaded = True
    
    # Validate media test (required)
    if not request.media_test_id:
        raise HTTPException(status_code=400, detail="Media test required before joining")
    
    if request.media_test_id not in media_tests:
        raise HTTPException(status_code=400, detail="Media test not found")
    
    media_test = media_tests[request.media_test_id]
    if not media_test["allowed_to_join"]:
        raise HTTPException(
            status_code=400, 
            detail="Media test failed. Please ensure your camera and microphone are working properly."
        )
    
    # Check for duplicate participants
    if meeting_id not in active_participants:
        active_participants[meeting_id] = set()
    
    participant_key = f"patient_{request.patient_name.lower()}"
    if participant_key in active_participants[meeting_id]:
        raise HTTPException(status_code=409, detail="Patient already in meeting")
    
    # Add patient to active participants
    active_participants[meeting_id].add(participant_key)
    
    try:
        # Generate token for patient with limited permissions
        token = livekit_client.generate_token(
            room_name=meeting_data["room_name"],
            participant_name=f"Patient: {request.patient_name}",
            is_host=False,
            metadata={"role": "patient", "permissions": ["participant"]}
        )
        
        # Update meeting data with patient information
        meeting_data.update({
            "patient_name": request.patient_name,
            "patient_joined": True,
            "patient_setup_completed": True,
            "document_uploaded": document_uploaded,
            "media_test_completed": True
        })
        
        # Add patient to participants list
        meeting_data["participants"].append({
            "name": request.patient_name,
            "role": "patient",
            "joined_at": datetime.now().isoformat(),
            "document_id": request.document_id,
            "media_test_id": request.media_test_id
        })
        
        participants_count = len(meeting_data["participants"])
        
        logger.info(f"Patient {request.patient_name} joined meeting {meeting_id}")
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=f"{get_base_url()}/meeting/{meeting_id}",
            livekit_url=livekit_client.livekit_url,
            token=token,
            participants_count=participants_count,
            user_role="patient",
            meeting_status={
                "doctor_name": meeting_data["doctor_name"],
                "patient_setup_completed": True,
                "document_uploaded": document_uploaded,
                "media_test_completed": True
            }
        )
        
    except Exception as e:
        # Remove from active participants if token generation fails
        active_participants[meeting_id].discard(participant_key)
        logger.error(f"Failed to generate token for patient {request.patient_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to join meeting")

@app.get("/api/meetings/{meeting_id}/status", response_model=MeetingStatusResponse)
async def get_meeting_status(meeting_id: str):
    """Get detailed meeting status for role-based UI updates"""
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting = meetings[meeting_id]
    
    # Check if patient has completed setup
    patient_setup_completed = (
        meeting.get("patient_name") is not None and
        meeting.get("media_test_completed", False)
    )
    
    # Check if documents were uploaded
    document_uploaded = any(
        doc["meeting_id"] == meeting_id 
        for doc in patient_documents.values()
    )
    
    return MeetingStatusResponse(
        meeting_id=meeting_id,
        doctor_name=meeting["doctor_name"],
        doctor_joined=meeting.get("doctor_joined", False),
        patient_name=meeting.get("patient_name"),
        patient_joined=meeting.get("patient_joined", False),
        patient_setup_completed=patient_setup_completed,
        document_uploaded=document_uploaded,
        media_test_completed=meeting.get("media_test_completed", False),
        meeting_active=meeting.get("meeting_active", True),
        created_at=meeting["created_at"]
    )

@app.post("/api/meetings/{meeting_id}/join-doctor", response_model=MeetingResponse)
async def doctor_join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Doctor join meeting - bypasses patient validation requirements"""
    
    # Validate meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting_data = meetings[meeting_id]
    
    # Validate this is actually a doctor joining
    if request.participant_role != "doctor":
        raise HTTPException(status_code=400, detail="This endpoint is for doctors only")
    
    # Check if this is the original doctor or another doctor
    is_original_doctor = request.participant_name == meeting_data["doctor_name"]
    
    if not is_original_doctor:
        # For now, only allow the original doctor
        # Later you could extend this for multiple doctors
        raise HTTPException(status_code=403, detail="Only the original doctor can join this meeting")
    
    # Check for duplicate participants
    if meeting_id not in active_participants:
        active_participants[meeting_id] = set()
    
    participant_key = f"doctor_{request.participant_name.lower()}"
    
    try:
        # Generate token for doctor with admin permissions
        token = livekit_client.generate_token(
            room_name=meeting_data["room_name"],
            participant_name=f"Dr. {request.participant_name}",
            is_host=True,
            metadata={"role": "doctor", "permissions": ["admin", "record", "moderate"]}
        )
        
        # Update meeting status
        meeting_data["doctor_joined"] = True
        
        # Add to active participants if not already there
        active_participants[meeting_id].add(participant_key)
        
        # Update participant in the list if needed
        for participant in meeting_data["participants"]:
            if participant["name"] == request.participant_name and participant["role"] == "doctor":
                participant["joined_at"] = datetime.now().isoformat()
                participant["token_generated"] = True
                break
        
        participants_count = len(meeting_data["participants"])
        
        logger.info(f"Doctor {request.participant_name} joined meeting {meeting_id}")
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=f"{get_base_url()}/meeting/{meeting_id}",
            livekit_url=livekit_client.url,
            token=token,
            participants_count=participants_count,
            user_role="doctor",
            meeting_status={
                "doctor_name": meeting_data["doctor_name"],
                "patient_name": meeting_data.get("patient_name"),
                "patient_setup_completed": meeting_data.get("patient_setup_completed", False),
                "document_uploaded": meeting_data.get("document_uploaded", False),
                "media_test_completed": meeting_data.get("media_test_completed", False)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate token for doctor {request.participant_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to join meeting")

@app.get("/doctor-dashboard/{meeting_id}", response_class=HTMLResponse)
async def doctor_dashboard(meeting_id: str):
    """Serve the doctor dashboard to monitor patient setup and meeting status"""
    # Validate meeting exists
    if meeting_id not in meetings:
        return HTMLResponse(
            content="<h1>Meeting not found</h1><p>The meeting you're looking for doesn't exist or has expired.</p>",
            status_code=404
        )
    
    try:
        with open("frontend/doctor_dashboard.html", "r", encoding='utf-8') as f:
            html_content = f.read()
            # Replace placeholder with actual meeting ID
            html_content = html_content.replace("{{MEETING_ID}}", meeting_id)
            return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("doctor_dashboard.html not found")
        # Return a simple dashboard if template doesn't exist
        meeting_data = meetings[meeting_id]
        patient_setup_url = f"{get_base_url()}/patient-setup?meeting={meeting_id}"
        
        simple_dashboard = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Doctor Dashboard - Meeting {meeting_id}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .status.completed {{ background-color: #d4edda; color: #155724; }}
                .status.pending {{ background-color: #fff3cd; color: #856404; }}
                .status.missing {{ background-color: #f8d7da; color: #721c24; }}
                .url-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .url-box input {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
                button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <h1>Doctor Dashboard</h1>
            <h2>Meeting: {meeting_id}</h2>
            <p><strong>Doctor:</strong> Dr. {meeting_data["doctor_name"]}</p>
            
            <h3>Patient Setup Status</h3>
            <div id="status-container">
                <div class="status pending">Loading status...</div>
            </div>
            
            <h3>Patient Setup Link</h3>
            <div class="url-box">
                <label>Send this link to your patient:</label>
                <input type="text" value="{patient_setup_url}" readonly onclick="this.select()">
                <button onclick="copyToClipboard()">Copy Link</button>
            </div>
            
            <h3>Actions</h3>
            <button onclick="joinMeeting()">Join Meeting Room</button>
            <button onclick="refreshStatus()">Refresh Status</button>
            
            <script>
                function copyToClipboard() {{
                    const input = document.querySelector('input[readonly]');
                    input.select();
                    document.execCommand('copy');
                    alert('Link copied to clipboard!');
                }}
                
                function joinMeeting() {{
                    window.open('/meeting/{meeting_id}?role=doctor', '_blank');
                }}
                
                async function refreshStatus() {{
                    try {{
                        const response = await fetch('/api/meetings/{meeting_id}/status');
                        const status = await response.json();
                        updateStatusDisplay(status);
                    }} catch (error) {{
                        console.error('Error fetching status:', error);
                    }}
                }}
                
                function updateStatusDisplay(status) {{
                    const container = document.getElementById('status-container');
                    container.innerHTML = `
                        <div class="status ${{status.patient_setup_completed ? 'completed' : 'pending'}}">
                            Patient Setup: ${{status.patient_setup_completed ? 'Completed' : 'Pending'}}
                        </div>
                        <div class="status ${{status.document_uploaded ? 'completed' : 'missing'}}">
                            Document Upload: ${{status.document_uploaded ? 'Uploaded' : 'Not uploaded'}}
                        </div>
                        <div class="status ${{status.media_test_completed ? 'completed' : 'pending'}}">
                            Media Test: ${{status.media_test_completed ? 'Completed' : 'Pending'}}
                        </div>
                        <div class="status ${{status.patient_joined ? 'completed' : 'pending'}}">
                            Patient Joined: ${{status.patient_joined ? 'Yes' : 'No'}}
                        </div>
                    `;
                    if (status.patient_name) {{
                        container.innerHTML += `<p><strong>Patient Name:</strong> ${{status.patient_name}}</p>`;
                    }}
                }}
                
                // Auto-refresh every 5 seconds
                setInterval(refreshStatus, 5000);
                refreshStatus(); // Initial load
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=simple_dashboard)

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