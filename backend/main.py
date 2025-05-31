import os
import random
import string
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from livekit_client import LiveKitClient

# Get the directory containing this file and the parent directory (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Initialize FastAPI app
app = FastAPI(title="HeyDok Video - Simple Video Meetings")

# Configure CORS - restrict in production
allowed_origins = ["*"]  # Change this in production!
if os.getenv("APP_URL"):
    # In production, only allow the app's own origin
    app_url = os.getenv("APP_URL")
    allowed_origins = [app_url, f"{app_url}/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(project_root, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Initialize LiveKit client
livekit = LiveKitClient()

# In-memory storage for meetings
meetings: Dict[str, dict] = {}

# Request/Response models
class CreateMeetingRequest(BaseModel):
    host_name: str = "Host"

class JoinMeetingRequest(BaseModel):
    participant_name: str

class MeetingResponse(BaseModel):
    meeting_id: str
    meeting_url: str
    livekit_url: str
    token: str

def generate_meeting_id() -> str:
    """Generate a readable meeting ID format: xxx-yyyy-zzz"""
    parts = []
    for length in [3, 4, 3]:
        part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        parts.append(part)
    return '-'.join(parts)

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve the homepage"""
    try:
        frontend_path = os.path.join(project_root, "frontend", "index.html")
        with open(frontend_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Homepage not found. Please create frontend/index.html</h1>"

@app.post("/api/meetings", response_model=MeetingResponse)
async def create_meeting(request: CreateMeetingRequest):
    """Create a new meeting"""
    meeting_id = generate_meeting_id()
    room_name = livekit.get_room_name(meeting_id)
    
    # Generate host token
    token = livekit.generate_token(
        room_name=room_name,
        participant_name=request.host_name,
        is_host=True
    )
    
    # Store meeting in memory
    meetings[meeting_id] = {
        "id": meeting_id,
        "room_name": room_name,
        "created_at": datetime.now().isoformat(),
        "host_name": request.host_name,
        "participants": []
    }
    
    # Get base URL - properly handle production URL
    base_url = os.getenv("APP_URL")
    if not base_url:
        # Fallback for local development
        base_url = "http://localhost:8000"
    
    return MeetingResponse(
        meeting_id=meeting_id,
        meeting_url=f"{base_url}/meeting/{meeting_id}",
        livekit_url=livekit.url,
        token=token
    )

@app.post("/api/meetings/{meeting_id}/join", response_model=MeetingResponse)
async def join_meeting(meeting_id: str, request: JoinMeetingRequest):
    """Join an existing meeting"""
    # Check if meeting exists
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting = meetings[meeting_id]
    room_name = meeting["room_name"]
    
    # Generate participant token
    token = livekit.generate_token(
        room_name=room_name,
        participant_name=request.participant_name,
        is_host=False
    )
    
    # Add participant to meeting
    meeting["participants"].append({
        "name": request.participant_name,
        "joined_at": datetime.now().isoformat()
    })
    
    # Get base URL - properly handle production URL
    base_url = os.getenv("APP_URL")
    if not base_url:
        # Fallback for local development
        base_url = "http://localhost:8000"
    
    return MeetingResponse(
        meeting_id=meeting_id,
        meeting_url=f"{base_url}/meeting/{meeting_id}",
        livekit_url=livekit.url,
        token=token
    )

@app.get("/meeting/{meeting_id}", response_class=HTMLResponse)
async def meeting_room(meeting_id: str):
    """Serve the meeting room page"""
    # Check if meeting exists
    if meeting_id not in meetings:
        return "<h1>Meeting not found</h1><p>This meeting does not exist or has expired.</p>"
    
    try:
        meeting_path = os.path.join(project_root, "frontend", "meeting.html")
        with open(meeting_path, "r") as f:
            html_content = f.read()
            # Inject meeting ID into the HTML
            html_content = html_content.replace("{{MEETING_ID}}", meeting_id)
            return html_content
    except FileNotFoundError:
        return "<h1>Meeting room not found. Please create frontend/meeting.html</h1>"

# Serve app.js from frontend directory
@app.get("/frontend/app.js")
async def serve_app_js():
    """Serve the app.js file"""
    try:
        app_js_path = os.path.join(project_root, "frontend", "app.js")
        with open(app_js_path, "r") as f:
            content = f.read()
            return HTMLResponse(content=content, media_type="application/javascript")
    except FileNotFoundError:
        return HTMLResponse(content="", status_code=404)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "meetings_count": len(meetings)}

# API Health check endpoint
@app.get("/api/health")
async def api_health_check():
    """API Health check endpoint"""
    return {"status": "healthy", "meetings_count": len(meetings)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 