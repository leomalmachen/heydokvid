"""
LiveKit client integration for WebRTC functionality
"""

import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from livekit import api, rtc
from livekit.api import AccessToken, VideoGrants

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import generate_secure_token

logger = get_logger(__name__)


class LiveKitClient:
    """
    LiveKit client wrapper for room and participant management
    """
    
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
        self.room_service: Optional[api.RoomServiceClient] = None
        self.egress_service: Optional[api.EgressServiceClient] = None
    
    async def initialize(self):
        """
        Initialize LiveKit service clients
        """
        try:
            # Initialize Room Service
            self.room_service = api.RoomServiceClient(
                self.url,
                self.api_key,
                self.api_secret
            )
            
            # Initialize Egress Service for recordings
            self.egress_service = api.EgressServiceClient(
                self.url,
                self.api_key,
                self.api_secret
            )
            
            logger.info("LiveKit clients initialized successfully", 
                       url=self.url, api_key=self.api_key[:8] + "...")
        except Exception as e:
            logger.error("Failed to initialize LiveKit clients", error=str(e))
            raise
    
    def create_token(
        self,
        room_name: str,
        participant_name: str,
        participant_identity: str,
        grants: Optional[VideoGrants] = None,
        metadata: Optional[str] = None,
        ttl: Optional[timedelta] = None
    ) -> str:
        """
        Create access token for participant
        """
        if not grants:
            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
                hidden=False,
            )
        
        token = AccessToken(self.api_key, self.api_secret)
        token.identity = participant_identity
        token.name = participant_name
        token.video_grants = grants
        
        if metadata:
            token.metadata = metadata
        
        if ttl:
            token.ttl = ttl
        else:
            token.ttl = timedelta(hours=24)
        
        jwt_token = token.to_jwt()
        logger.info("Token created for participant", 
                   room=room_name, participant=participant_identity)
        return jwt_token
    
    async def create_room(
        self,
        name: str,
        empty_timeout: int = 300,
        max_participants: int = 20,
        metadata: Optional[str] = None
    ) -> api.Room:
        """
        Create a new room on LiveKit server
        """
        try:
            # Check if room already exists
            existing_room = await self.get_room(name)
            if existing_room:
                logger.info("Room already exists", room_name=name, room_sid=existing_room.sid)
                return existing_room
            
            request = api.CreateRoomRequest(
                name=name,
                empty_timeout=empty_timeout,
                max_participants=max_participants,
                metadata=metadata or json.dumps({"type": "meeting"})
            )
            
            room = await self.room_service.create_room(request)
            logger.info("Room created successfully", 
                       room_name=name, room_sid=room.sid, max_participants=max_participants)
            return room
            
        except Exception as e:
            logger.error("Failed to create room", room_name=name, error=str(e))
            raise
    
    async def list_rooms(self, names: Optional[List[str]] = None) -> List[api.Room]:
        """
        List active rooms
        """
        try:
            request = api.ListRoomsRequest(names=names)
            response = await self.room_service.list_rooms(request)
            return response.rooms
        except Exception as e:
            logger.error("Failed to list rooms", error=str(e))
            return []
    
    async def get_room(self, room_name: str) -> Optional[api.Room]:
        """
        Get room by name
        """
        try:
            rooms = await self.list_rooms(names=[room_name])
            return rooms[0] if rooms else None
        except Exception as e:
            logger.error("Failed to get room", room_name=room_name, error=str(e))
            return None
    
    async def delete_room(self, room_name: str) -> bool:
        """
        Delete a room
        """
        try:
            request = api.DeleteRoomRequest(room=room_name)
            await self.room_service.delete_room(request)
            logger.info("Room deleted", room_name=room_name)
            return True
        except Exception as e:
            logger.error("Failed to delete room", room_name=room_name, error=str(e))
            return False
    
    async def list_participants(
        self,
        room_name: str
    ) -> List[api.ParticipantInfo]:
        """
        List participants in a room
        """
        try:
            request = api.ListParticipantsRequest(room=room_name)
            response = await self.room_service.list_participants(request)
            return response.participants
        except Exception as e:
            logger.error(
                "Failed to list participants",
                room_name=room_name,
                error=str(e)
            )
            return []
    
    async def get_participant(
        self,
        room_name: str,
        identity: str
    ) -> Optional[api.ParticipantInfo]:
        """
        Get participant by identity
        """
        try:
            request = api.GetParticipantRequest(
                room=room_name,
                identity=identity
            )
            return await self.room_service.get_participant(request)
        except Exception as e:
            logger.error(
                "Failed to get participant",
                room_name=room_name,
                identity=identity,
                error=str(e)
            )
            return None
    
    async def remove_participant(
        self,
        room_name: str,
        identity: str
    ) -> bool:
        """
        Remove participant from room
        """
        try:
            request = api.RemoveParticipantRequest(
                room=room_name,
                identity=identity
            )
            await self.room_service.remove_participant(request)
            logger.info(
                "Participant removed",
                room_name=room_name,
                identity=identity
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to remove participant",
                room_name=room_name,
                identity=identity,
                error=str(e)
            )
            return False
    
    async def mute_published_track(
        self,
        room_name: str,
        identity: str,
        track_sid: str,
        muted: bool
    ) -> api.TrackInfo:
        """
        Mute/unmute a published track
        """
        try:
            request = api.MuteRoomTrackRequest(
                room=room_name,
                identity=identity,
                track_sid=track_sid,
                muted=muted
            )
            return await self.room_service.mute_published_track(request)
        except Exception as e:
            logger.error(
                "Failed to mute track",
                room_name=room_name,
                identity=identity,
                track_sid=track_sid,
                error=str(e)
            )
            raise
    
    async def update_participant(
        self,
        room_name: str,
        identity: str,
        metadata: Optional[str] = None,
        permission: Optional[api.ParticipantPermission] = None
    ) -> api.ParticipantInfo:
        """
        Update participant metadata or permissions
        """
        try:
            request = api.UpdateParticipantRequest(
                room=room_name,
                identity=identity,
                metadata=metadata,
                permission=permission
            )
            return await self.room_service.update_participant(request)
        except Exception as e:
            logger.error(
                "Failed to update participant",
                room_name=room_name,
                identity=identity,
                error=str(e)
            )
            raise
    
    async def start_room_recording(
        self,
        room_name: str,
        output_path: str,
        audio_only: bool = False
    ) -> str:
        """
        Start recording a room
        """
        try:
            # Create file output configuration
            file_output = api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath=output_path
            )
            
            # Create recording request
            request = api.RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=audio_only,
                file=file_output
            )
            
            response = await self.egress_service.start_room_composite_egress(request)
            logger.info(
                "Room recording started",
                room_name=room_name,
                egress_id=response.egress_id
            )
            return response.egress_id
            
        except Exception as e:
            logger.error(
                "Failed to start room recording",
                room_name=room_name,
                error=str(e)
            )
            raise
    
    async def stop_recording(self, egress_id: str) -> api.EgressInfo:
        """
        Stop an active recording
        """
        try:
            request = api.StopEgressRequest(egress_id=egress_id)
            response = await self.egress_service.stop_egress(request)
            logger.info("Recording stopped", egress_id=egress_id)
            return response
        except Exception as e:
            logger.error(
                "Failed to stop recording",
                egress_id=egress_id,
                error=str(e)
            )
            raise
    
    def generate_room_name(self) -> str:
        """
        Generate unique room name in Google Meet style (xxx-xxxx-xxx)
        """
        import secrets
        import string
        
        chars = string.ascii_lowercase + string.digits
        parts = [
            ''.join(secrets.choice(chars) for _ in range(3)),
            ''.join(secrets.choice(chars) for _ in range(4)),
            ''.join(secrets.choice(chars) for _ in range(3))
        ]
        return '-'.join(parts)
    
    def create_participant_token(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        role: str = "participant",
        can_publish: bool = True,
        can_subscribe: bool = True,
        can_publish_data: bool = True,
        hidden: bool = False,
        recorder: bool = False
    ) -> str:
        """
        Create participant token with specific permissions
        """
        grants = VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
            can_publish_data=can_publish_data,
            hidden=hidden,
            recorder=recorder
        )
        
        metadata = {
            "role": role,
            "user_id": user_id,
            "timestamp": int(time.time())
        }
        
        return self.create_token(
            room_name=room_name,
            participant_name=user_name,
            participant_identity=user_id,
            grants=grants,
            metadata=json.dumps(metadata)
        )


# Global LiveKit client instance
livekit_client = LiveKitClient()


# Helper functions
def get_livekit_client() -> LiveKitClient:
    """
    Get LiveKit client for dependency injection
    """
    return livekit_client 