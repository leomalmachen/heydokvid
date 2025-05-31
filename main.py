import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
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

# Cleanup old meetings periodically (simple in-memory cleanup)
def cleanup_old_meetings():
    """Remove meetings older than 24 hours"""
    now = datetime.now()
    expired_meetings = []
    
    for meeting_id, meeting_data in meetings.items():
        created_at = datetime.fromisoformat(meeting_data["created_at"])
        if now - created_at > timedelta(hours=24):
            expired_meetings.append(meeting_id)
    
    for meeting_id in expired_meetings:
        del meetings[meeting_id]
        logger.info(f"Cleaned up expired meeting: {meeting_id}")
    
    logger.info(f"Active meetings: {len(meetings)}")

# Request/Response models
class CreateMeetingRequest(BaseModel):
    host_name: str = Field(default="Host", min_length=1, max_length=50)

class JoinMeetingRequest(BaseModel):
    participant_name: str = Field(min_length=1, max_length=50)

class MeetingResponse(BaseModel):
    meeting_id: str
    meeting_url: str
    livekit_url: str
    token: str
    participants_count: int = 0

class HealthResponse(BaseModel):
    status: str
    app_version: str = "1.0.0"
    meetings_count: int
    livekit_connected: bool
    timestamp: str

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
    """Serve the homepage"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            # Inject base URL for API calls
            content = content.replace("{{BASE_URL}}", get_base_url())
            return content
    except FileNotFoundError:
        logger.error("Homepage file not found: frontend/index.html")
        return HTMLResponse(
            content="""
            <html>
                <head><title>HeyDok Video</title></head>
                <body>
                    <h1>HeyDok Video</h1>
                    <p>Frontend files not found. Please make sure frontend/index.html exists.</p>
                    <p><a href="/health">Check system health</a></p>
                </body>
            </html>
            """,
            status_code=200  # Return 200 so Heroku doesn't think the app is broken
        )
    except Exception as e:
        logger.error(f"Error serving homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/meetings", response_model=MeetingResponse)
async def create_meeting(
    request: CreateMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Create a new meeting"""
    try:
        # Clean up old meetings before creating new ones
        cleanup_old_meetings()
        
        meeting_id = generate_meeting_id()
        room_name = livekit_client.get_room_name(meeting_id)
        
        logger.info(f"Creating meeting {meeting_id} for host {request.host_name}")
        
        # Generate host token
        token = livekit_client.generate_token(
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
            "participants": [],
            "is_active": True
        }
        
        base_url = get_base_url()
        meeting_url = f"{base_url}/meeting/{meeting_id}"
        
        logger.info(f"Meeting {meeting_id} created successfully. URL: {meeting_url}")
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            livekit_url=livekit_client.url,
            token=token,
            participants_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

@app.post("/api/meetings/{meeting_id}/join", response_model=MeetingResponse)
async def join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit_client: LiveKitClient = Depends(get_livekit_client)
):
    """Join an existing meeting"""
    try:
        # Check if meeting exists, create if not (handles Heroku memory loss)
        if meeting_id not in meetings:
            logger.info(f"Meeting {meeting_id} not found in memory, creating entry for join request")
            # Create meeting entry for this meeting ID
            meetings[meeting_id] = {
                "id": meeting_id,
                "room_name": f"meeting-{meeting_id}",
                "created_at": datetime.now().isoformat(),
                "host_name": "Host",
                "participants": [],
                "is_active": True
            }
        
        meeting = meetings[meeting_id]
        room_name = meeting["room_name"]
        
        logger.info(f"User {request.participant_name} joining meeting {meeting_id}")
        
        # Generate participant token
        token = livekit_client.generate_token(
            room_name=room_name,
            participant_name=request.participant_name,
            is_host=False
        )
        
        # Add participant to meeting
        participant_info = {
            "name": request.participant_name,
            "joined_at": datetime.now().isoformat()
        }
        meeting["participants"].append(participant_info)
        
        base_url = get_base_url()
        meeting_url = f"{base_url}/meeting/{meeting_id}"
        
        logger.info(f"User {request.participant_name} joined meeting {meeting_id} successfully")
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            livekit_url=livekit_client.url,
            token=token,
            participants_count=len(meeting["participants"])
        )
        
    except Exception as e:
        logger.error(f"Error joining meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to join meeting: {str(e)}")

@app.get("/meeting/{meeting_id}", response_class=HTMLResponse)
async def meeting_room(meeting_id: str):
    """Serve the meeting room page"""
    try:
        # Check if meeting exists
        if meeting_id not in meetings:
            logger.warning(f"Attempt to access non-existent meeting room: {meeting_id}")
            return HTMLResponse(
                content="<h1>Meeting not found</h1><p>This meeting does not exist or has expired.</p>",
                status_code=404
            )
        
        with open("frontend/meeting.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            # Inject meeting ID and base URL
            html_content = html_content.replace("{{MEETING_ID}}", meeting_id)
            html_content = html_content.replace("{{BASE_URL}}", get_base_url())
            return html_content
            
    except FileNotFoundError:
        logger.error("Meeting room file not found: frontend/meeting.html")
        return HTMLResponse(
            content="<h1>Meeting room not found</h1><p>Please create frontend/meeting.html</p>",
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error serving meeting room {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
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