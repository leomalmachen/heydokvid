import os
import time
from livekit import AccessToken, VideoGrant
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LiveKitClient:
    def __init__(self):
        self.url = os.getenv('LIVEKIT_URL')
        self.api_key = os.getenv('LIVEKIT_API_KEY')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET')
        
        if not all([self.url, self.api_key, self.api_secret]):
            raise ValueError("LiveKit credentials not properly configured")
    
    def generate_token(self, room_name: str, participant_name: str, is_host: bool = False) -> str:
        """Generate an access token for a participant to join a room"""
        token = AccessToken(self.api_key, self.api_secret)
        
        # Basic participant info
        token.identity = participant_name
        token.name = participant_name
        
        # Grant room permissions
        grant = VideoGrant(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        
        # Host gets additional permissions
        if is_host:
            grant.room_admin = True
            grant.room_record = True
        
        token.add_grant(grant)
        
        # Set expiration (24 hours)
        token.ttl = 86400
        
        return token.to_jwt()
    
    def get_room_name(self, meeting_id: str) -> str:
        """Convert meeting ID to LiveKit room name"""
        return f"meeting-{meeting_id}" 