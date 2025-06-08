import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
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
    title="🏥 HeyDok Video - Simple Version",
    description="Simplified video meeting app for testing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Initialize LiveKit client
try:
    livekit = LiveKitClient()
    if livekit.validate_credentials():
        logger.info("LiveKit client initialized and validated successfully")
    else:
        logger.error("LiveKit credentials validation failed")
        raise Exception("Invalid LiveKit credentials")
except Exception as e:
    logger.error(f"Failed to initialize LiveKit client: {e}")
    livekit = None

# In-memory storage for meetings
meetings: Dict[str, dict] = {}

# Pydantic models
class JoinMeetingRequest(BaseModel):
    participant_name: str = Field(min_length=1, max_length=50)
    participant_role: str = Field(default="patient", pattern="^(doctor|patient)$")

class MeetingResponse(BaseModel):
    meeting_id: str
    meeting_url: str
    livekit_url: str
    token: str
    participants_count: int = 0
    user_role: str

def generate_meeting_id() -> str:
    """Generate a unique meeting ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

def get_livekit_client() -> LiveKitClient:
    if not livekit:
        raise HTTPException(status_code=503, detail="LiveKit service unavailable")
    return livekit

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Simple homepage with meeting creation"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HeyDok Video - Simple</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .btn { background: #4285f4; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; }
            .btn:hover { background: #3367d6; }
            input { padding: 10px; margin: 10px; border: 1px solid #ddd; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🏥 HeyDok Video - Simple Test</h1>
        <p>Vereinfachte Version zum Testen des Video-Streamings</p>
        
        <div>
            <h2>Neues Meeting erstellen</h2>
            <button class="btn" onclick="createMeeting()">Meeting erstellen</button>
        </div>
        
        <div id="meeting-info" style="display: none; margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 5px;">
            <h3>Meeting erstellt!</h3>
            <p><strong>Meeting ID:</strong> <span id="meeting-id"></span></p>
            <p><strong>Arzt-Link:</strong> <a id="doctor-link" href="#" target="_blank">Als Arzt beitreten</a></p>
            <p><strong>Patient-Link:</strong> <a id="patient-link" href="#" target="_blank">Als Patient beitreten</a></p>
        </div>
        
        <script>
            async function createMeeting() {
                try {
                    const response = await fetch('/api/create-simple-meeting', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({})
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('meeting-id').textContent = data.meeting_id;
                        document.getElementById('doctor-link').href = `/simple-meeting/${data.meeting_id}?role=doctor`;
                        document.getElementById('patient-link').href = `/simple-meeting/${data.meeting_id}?role=patient`;
                        document.getElementById('meeting-info').style.display = 'block';
                    } else {
                        alert('Fehler beim Erstellen des Meetings');
                    }
                } catch (error) {
                    alert('Fehler: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """)

@app.post("/api/create-simple-meeting")
async def create_simple_meeting():
    """Create a simple meeting for testing"""
    meeting_id = generate_meeting_id()
    
    # Store meeting
    meetings[meeting_id] = {
        "meeting_id": meeting_id,
        "created_at": datetime.utcnow().isoformat(),
        "participants": []
    }
    
    logger.info(f"Created simple meeting: {meeting_id}")
    
    return {
        "meeting_id": meeting_id,
        "doctor_url": f"/simple-meeting/{meeting_id}?role=doctor",
        "patient_url": f"/simple-meeting/{meeting_id}?role=patient"
    }

@app.post("/api/meetings/{meeting_id}/join", response_model=MeetingResponse)
async def join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Join a meeting"""
    # Check if meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting = meetings[meeting_id]
    
    # Generate LiveKit token
    room_name = f"meeting-{meeting_id}"
    is_host = request.participant_role == "doctor"
    
    try:
        token = livekit_client.generate_token(
            room_name=room_name,
            participant_name=request.participant_name,
            is_host=is_host
        )
        
        # Add participant to meeting
        participant_info = {
            "name": request.participant_name,
            "role": request.participant_role,
            "joined_at": datetime.utcnow().isoformat()
        }
        meeting["participants"].append(participant_info)
        
        logger.info(f"Participant {request.participant_name} joined meeting {meeting_id} as {request.participant_role}")
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=f"/simple-meeting/{meeting_id}",
            livekit_url=livekit_client.url,
            token=token,
            participants_count=len(meeting["participants"]),
            user_role=request.participant_role
        )
        
    except Exception as e:
        logger.error(f"Error joining meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to join meeting: {str(e)}")

@app.get("/simple-meeting/{meeting_id}", response_class=HTMLResponse)
async def simple_meeting_room(meeting_id: str):
    """Serve the simple meeting room"""
    # Check if meeting exists
    if meeting_id not in meetings:
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
                <p>Datei frontend/simple_meeting.html nicht gefunden.</p>
            </body>
            </html>
            """,
            status_code=503
        )

@app.get("/frontend/simple_meeting.js")
async def serve_simple_meeting_js():
    """Serve the simple meeting JavaScript"""
    try:
        with open("frontend/simple_meeting.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        return Response(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JavaScript file not found")

@app.get("/api/meetings/{meeting_id}/info")
async def get_meeting_info(meeting_id: str):
    """Get meeting information"""
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting = meetings[meeting_id]
    return {
        "meeting_id": meeting_id,
        "livekit_url": livekit.url if livekit else None,
        "participants_count": len(meeting.get("participants", [])),
        "created_at": meeting.get("created_at")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "meetings_count": len(meetings),
        "livekit_connected": livekit is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting HeyDok Video Simple on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    ) 