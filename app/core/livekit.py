"""
LiveKit client integration for WebRTC functionality
"""

import os
import time
import secrets
import string
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from livekit import api
from livekit.api import AccessToken, VideoGrants, RoomServiceClient
import structlog

logger = structlog.get_logger()


class LiveKitClient:
    """
    LiveKit client wrapper for room and participant management
    """
    
    def __init__(self):
        self.api_key = os.getenv('LIVEKIT_API_KEY', 'devkey')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET', 'secret')
        self.url = os.getenv('LIVEKIT_URL', 'ws://localhost:7880')
        
        # Convert ws:// to http:// for API calls
        self.api_url = self.url.replace('ws://', 'http://').replace('wss://', 'https://')
        
        self.room_service: Optional[RoomServiceClient] = None
        self._initialized = False
        
    async def initialize(self):
        """
        Initialize LiveKit service clients
        """
        if self._initialized:
            return
            
        try:
            # Initialize Room Service Client
            self.room_service = RoomServiceClient(
                self.api_url,
                self.api_key,
                self.api_secret
            )
            
            self._initialized = True
            logger.info("LiveKit clients initialized successfully",
                       url=self.url,
                       api_key=self.api_key[:10] + "...")
        except Exception as e:
            logger.error("Failed to initialize LiveKit clients", error=str(e))
            raise
    
    def generate_room_id(self) -> str:
        """
        Generate a unique room ID in format: xxx-xxxx-xxx
        """
        parts = []
        for length in [3, 4, 3]:
            part = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))
            parts.append(part)
        return '-'.join(parts)
    
    def generate_token(
        self,
        room_name: str,
        identity: str,
        name: str = None,
        metadata: Dict[str, Any] = None,
        can_publish: bool = True,
        can_subscribe: bool = True,
        can_publish_data: bool = True,
        validity_hours: int = 24
    ) -> str:
        """
        Generate an access token for a participant
        """
        try:
            # Create access token
            token = AccessToken(self.api_key, self.api_secret)
            
            # Set token properties
            token.identity = identity
            token.name = name or identity
            
            if metadata:
                token.metadata = str(metadata)
            
            # Set video grants
            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=can_publish,
                can_subscribe=can_subscribe,
                can_publish_data=can_publish_data
            )
            token.add_grant(grants)
            
            # Set expiration
            token.ttl = timedelta(hours=validity_hours)
            
            # Generate JWT token
            jwt_token = token.to_jwt()
            
            logger.info("Generated LiveKit token",
                       room=room_name,
                       identity=identity,
                       can_publish=can_publish)
            
            return jwt_token
            
        except Exception as e:
            logger.error("Failed to generate token",
                        error=str(e),
                        room=room_name,
                        identity=identity)
            raise
    
    async def create_room(
        self,
        room_name: str,
        empty_timeout: int = 300,
        max_participants: int = 50,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new room on LiveKit server
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create room using RoomService
            room = await self.room_service.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=empty_timeout,
                    max_participants=max_participants,
                    metadata=str(metadata) if metadata else None
                )
            )
            
            logger.info("Created LiveKit room",
                       room_name=room_name,
                       max_participants=max_participants)
            
            return {
                "name": room.name,
                "sid": room.sid,
                "creation_time": room.creation_time,
                "empty_timeout": room.empty_timeout,
                "max_participants": room.max_participants,
                "metadata": room.metadata
            }
            
        except Exception as e:
            logger.error("Failed to create room",
                        error=str(e),
                        room_name=room_name)
            raise
    
    async def get_room(self, room_name: str) -> Optional[Dict[str, Any]]:
        """
        Get room information
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # List all rooms and find the one we're looking for
            rooms = await self.room_service.list_rooms(api.ListRoomsRequest())
            
            for room in rooms.rooms:
                if room.name == room_name:
                    return {
                        "name": room.name,
                        "sid": room.sid,
                        "creation_time": room.creation_time,
                        "empty_timeout": room.empty_timeout,
                        "max_participants": room.max_participants,
                        "num_participants": room.num_participants,
                        "metadata": room.metadata
                    }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get room",
                        error=str(e),
                        room_name=room_name)
            return None
    
    async def delete_room(self, room_name: str) -> bool:
        """
        Delete a room
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            await self.room_service.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            
            logger.info("Deleted LiveKit room", room_name=room_name)
            return True
            
        except Exception as e:
            logger.error("Failed to delete room",
                        error=str(e),
                        room_name=room_name)
            return False
    
    async def list_participants(self, room_name: str) -> List[Dict[str, Any]]:
        """
        List all participants in a room
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            participants = await self.room_service.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )
            
            return [
                {
                    "sid": p.sid,
                    "identity": p.identity,
                    "name": p.name,
                    "state": p.state,
                    "metadata": p.metadata,
                    "joined_at": p.joined_at,
                    "is_publisher": p.is_publisher
                }
                for p in participants.participants
            ]
            
        except Exception as e:
            logger.error("Failed to list participants",
                        error=str(e),
                        room_name=room_name)
            return []
    
    async def remove_participant(self, room_name: str, identity: str) -> bool:
        """
        Remove a participant from a room
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            await self.room_service.remove_participant(
                api.RoomParticipantIdentity(
                    room=room_name,
                    identity=identity
                )
            )
            
            logger.info("Removed participant from room",
                       room_name=room_name,
                       identity=identity)
            return True
            
        except Exception as e:
            logger.error("Failed to remove participant",
                        error=str(e),
                        room_name=room_name,
                        identity=identity)
            return False


# Global LiveKit client instance
livekit_client = LiveKitClient()


def get_livekit_client() -> LiveKitClient:
    """
    Get LiveKit client for dependency injection
    """
    return livekit_client 