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
            raise ValueError('LiveKit credentials not properly configured')
    
    def generate_token(self, room_name: str, participant_name: str, is_host: bool = False) -> str:
        token = AccessToken(self.api_key, self.api_secret)
        token.identity = participant_name
        token.name = participant_name
        
        grant = VideoGrant(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        
        if is_host:
            grant.room_admin = True
            grant.room_record = True
        
        token.add_grant(grant)
        token.ttl = 86400
        
        return token.to_jwt()
    
    def get_room_name(self, meeting_id: str) -> str:
        return f'meeting-{meeting_id}'
    
    def validate_credentials(self) -> bool:
        try:
            test_token = AccessToken(self.api_key, self.api_secret)
            test_token.identity = 'test'
            test_token.name = 'test'
            test_token.ttl = 60
            
            grant = VideoGrant(room_join=True, room='test')
            test_token.add_grant(grant)
            
            test_token.to_jwt()
            return True
        except Exception:
            return False