"""
LiveKit client for video conferencing with enhanced security
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from livekit import api
import structlog
import jwt

from app.core.config import settings

logger = structlog.get_logger()


class LiveKitClient:
    """
    Enhanced LiveKit client for managing video conferences
    with improved security and error handling
    """
    
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
        self._client: Optional[api.LiveKitAPI] = None
        
        # Validate configuration
        if not all([self.api_key, self.api_secret, self.url]):
            raise ValueError("LiveKit configuration incomplete")
    
    async def initialize(self):
        """Initialize the LiveKit client with connection validation"""
        try:
            self._client = api.LiveKitAPI(
                url=self.url,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # Test connection by listing rooms
            await self._client.room.list_rooms(api.ListRoomsRequest())
            logger.info("LiveKit client initialized and connection verified", url=self.url)
        except Exception as e:
            logger.error("Failed to initialize LiveKit client", error=str(e))
            raise
    
    async def create_room(self, room_name: str, max_participants: int = 10, 
                         enable_recording: bool = False) -> Dict[str, Any]:
        """Create a new room with enhanced configuration"""
        try:
            if not self._client:
                await self.initialize()
            
            # Validate room name
            if not room_name or len(room_name) < 3:
                raise ValueError("Room name must be at least 3 characters")
            
            room_create = api.CreateRoomRequest(
                name=room_name,
                max_participants=max_participants,
                empty_timeout=300,  # 5 minutes
                metadata=f'{{"created_at": "{datetime.utcnow().isoformat()}", "enable_recording": {str(enable_recording).lower()}}}'
            )
            
            room = await self._client.room.create_room(room_create)
            
            logger.info("Room created successfully", 
                       room_name=room.name, 
                       room_sid=room.sid,
                       max_participants=max_participants)
            
            return {
                "room_name": room.name,
                "sid": room.sid,
                "max_participants": room.max_participants,
                "creation_time": room.creation_time,
                "url": self.url,
                "enable_recording": enable_recording
            }
        except Exception as e:
            logger.error("Failed to create room", room_name=room_name, error=str(e))
            raise
    
    async def generate_token(self, room_name: str, participant_name: str, 
                           user_role: str = "participant", 
                           can_publish: bool = True,
                           can_subscribe: bool = True,
                           can_publish_data: bool = True,
                           expires_in_minutes: int = 60,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate secure access token with role-based permissions"""
        try:
            # Validate inputs
            if not room_name or not participant_name:
                raise ValueError("Room name and participant name are required")
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            
            token = api.AccessToken(self.api_key, self.api_secret)
            token.with_identity(participant_name)
            token.with_name(participant_name)
            token.with_ttl(timedelta(minutes=expires_in_minutes))
            
            # Add metadata if provided
            if metadata:
                import json
                token.with_metadata(json.dumps(metadata))
            
            # Role-based permissions
            video_grants = api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=can_publish,
                can_subscribe=can_subscribe,
                can_publish_data=can_publish_data
            )
            
            # Enhanced permissions for physicians
            if user_role == "physician":
                video_grants.room_admin = True
                video_grants.room_record = True
                video_grants.can_update_own_metadata = True
            
            token.with_grants(video_grants)
            
            jwt_token = token.to_jwt()
            
            logger.info("Token generated successfully", 
                       room_name=room_name, 
                       participant_name=participant_name,
                       user_role=user_role,
                       expires_at=expires_at.isoformat(),
                       has_metadata=metadata is not None)
            
            return jwt_token
            
        except Exception as e:
            logger.error("Failed to generate token", 
                        room_name=room_name, 
                        participant_name=participant_name, 
                        error=str(e))
            raise
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate and decode a LiveKit token"""
        try:
            # Decode without verification first to get claims
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # Verify with secret
            payload = jwt.decode(token, self.api_secret, algorithms=["HS256"])
            
            return {
                "valid": True,
                "room_name": payload.get("video", {}).get("room"),
                "participant_name": payload.get("sub"),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "permissions": payload.get("video", {})
            }
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}
    
    async def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive room information"""
        try:
            if not self._client:
                await self.initialize()
            
            rooms = await self._client.room.list_rooms(api.ListRoomsRequest())
            
            for room in rooms.rooms:
                if room.name == room_name:
                    # Get participants
                    participants = await self._client.room.list_participants(
                        api.ListParticipantsRequest(room=room_name)
                    )
                    
                    return {
                        "room_name": room.name,
                        "sid": room.sid,
                        "num_participants": room.num_participants,
                        "max_participants": room.max_participants,
                        "creation_time": room.creation_time,
                        "url": self.url,
                        "participants": [
                            {
                                "identity": p.identity,
                                "name": p.name,
                                "joined_at": p.joined_at,
                                "is_publisher": p.permission.can_publish
                            } for p in participants.participants
                        ]
                    }
            
            return None
        except Exception as e:
            logger.error("Failed to get room info", room_name=room_name, error=str(e))
            return None
    
    async def room_exists(self, room_name: str) -> bool:
        """Check if room exists with better error handling"""
        try:
            room_info = await self.get_room_info(room_name)
            return room_info is not None
        except Exception as e:
            logger.error("Error checking room existence", room_name=room_name, error=str(e))
            return False
    
    async def delete_room(self, room_name: str) -> bool:
        """Delete a room (for cleanup)"""
        try:
            if not self._client:
                await self.initialize()
            
            await self._client.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            
            logger.info("Room deleted successfully", room_name=room_name)
            return True
        except Exception as e:
            logger.error("Failed to delete room", room_name=room_name, error=str(e))
            return False
    
    async def start_recording(self, room_name: str, output_file: str) -> Optional[str]:
        """Start recording a room"""
        try:
            if not self._client:
                await self.initialize()
            
            # Configure recording request
            recording_request = api.StartRecordingRequest(
                room_name=room_name,
                output={
                    "file": {
                        "filepath": output_file
                    }
                }
            )
            
            recording = await self._client.recording.start_recording(recording_request)
            
            logger.info("Recording started", 
                       room_name=room_name, 
                       recording_id=recording.recording_id)
            
            return recording.recording_id
        except Exception as e:
            logger.error("Failed to start recording", room_name=room_name, error=str(e))
            return None
    
    async def stop_recording(self, recording_id: str) -> bool:
        """Stop an active recording"""
        try:
            if not self._client:
                await self.initialize()
            
            await self._client.recording.stop_recording(
                api.StopRecordingRequest(recording_id=recording_id)
            )
            
            logger.info("Recording stopped", recording_id=recording_id)
            return True
        except Exception as e:
            logger.error("Failed to stop recording", recording_id=recording_id, error=str(e))
            return False


# Global instance
livekit_client = LiveKitClient() 