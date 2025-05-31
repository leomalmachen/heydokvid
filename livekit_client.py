import os
import time
from typing import Optional
from livekit import api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LiveKitClient:
    def __init__(self):
        self.url = os.getenv('LIVEKIT_URL')
        self.api_key = os.getenv('LIVEKIT_API_KEY')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET')
        
        if not all([self.url, self.api_key, self.api_secret]):
            raise ValueError(
                f"LiveKit credentials not properly configured. "
                f"URL: {'✓' if self.url else '✗'}, "
                f"API_KEY: {'✓' if self.api_key else '✗'}, "
                f"API_SECRET: {'✓' if self.api_secret else '✗'}"
            )
        
        print(f"LiveKit initialized with URL: {self.url}")
    
    def generate_token(self, room_name: str, participant_name: str, is_host: bool = False) -> str:
        """Generate an access token for a participant to join a room"""
        try:
            # Create access token using the new API
            token = api.AccessToken(self.api_key, self.api_secret)
            
            # Set participant identity and name
            token = token.with_identity(participant_name).with_name(participant_name)
            
            # Create video grants
            video_grants = api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
            
            # Add additional permissions for hosts
            if is_host:
                video_grants.room_admin = True
                video_grants.room_record = True
                video_grants.can_publish_sources = ["camera", "microphone", "screen_share"]
            
            # Add grants to token using the new API
            token = token.with_grants(video_grants)
            
            # Generate JWT
            jwt_token = token.to_jwt()
            print(f"Generated token for {participant_name} in room {room_name} (host: {is_host})")
            
            return jwt_token
            
        except Exception as e:
            print(f"Error generating token: {str(e)}")
            raise ValueError(f"Failed to generate LiveKit token: {str(e)}")
    
    def get_room_name(self, meeting_id: str) -> str:
        """Convert meeting ID to LiveKit room name"""
        # Ensure room name is valid (alphanumeric and hyphens only)
        room_name = f"meeting-{meeting_id}".lower()
        # Remove any invalid characters
        room_name = ''.join(c for c in room_name if c.isalnum() or c in ['-', '_'])
        return room_name
    
    def validate_credentials(self) -> bool:
        """Validate that LiveKit credentials are properly configured"""
        try:
            # Try to create a test token
            test_token = api.AccessToken(self.api_key, self.api_secret)
            test_token = test_token.with_identity("test").with_name("test")
            
            grants = api.VideoGrants(room_join=True, room="test")
            test_token = test_token.with_grants(grants)
            
            jwt = test_token.to_jwt()
            return True
        except Exception as e:
            print(f"LiveKit credentials validation failed: {str(e)}")
            return False 