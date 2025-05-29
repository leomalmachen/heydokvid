from fastapi import APIRouter, HTTPException
from datetime import datetime
import secrets
import string
from app.core.grok_client import grok_client
from pydantic import BaseModel
import os

router = APIRouter()

# Use new ngrok URL for public access
BASE_URL = "https://f2f9-217-138-216-222.ngrok-free.app"

def generate_meeting_code():
    """Generates a meeting code like xxx-xxxx-xxx"""
    parts = []
    for length in [3, 4, 3]:
        part = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))
        parts.append(part)
    return '-'.join(parts)

class JoinMeetingRequest(BaseModel):
    user_name: str

@router.post("/api/meetings/create")
async def create_instant_meeting():
    """One click = One meeting (like Google Meet)"""
    # Simple meeting code
    meeting_code = generate_meeting_code()
    
    # Create Grok room
    try:
        room = await grok_client.create_room(
            room_name=meeting_code,
            empty_timeout=3600,  # Room stays 1 hour after last participant
            max_participants=50
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Grok room: {str(e)}")
    
    # Generate public meeting link using ngrok URL
    meeting_link = f"{BASE_URL}/meet/{meeting_code}"
    
    return {
        "meetingCode": meeting_code,
        "meetingLink": meeting_link,
        "createdAt": datetime.utcnow().isoformat()
    }

@router.post("/api/meetings/join/{meeting_code}")
async def join_meeting(meeting_code: str, request: JoinMeetingRequest):
    """Join with just a name - no account needed"""
    # Check if room exists
    room = await grok_client.get_room(meeting_code)
    if not room:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Generate unique user ID
    user_id = f"{request.user_name.lower().replace(' ', '_')}_{secrets.token_hex(4)}"
    
    # Generate token
    try:
        token = grok_client.generate_token(
            room_name=meeting_code,
            identity=user_id,
            user_role="participant",
            metadata={"name": request.user_name}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")
    
    return {
        "token": token,
        "meetingCode": meeting_code,
        "userName": request.user_name
    } 