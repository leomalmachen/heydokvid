import os
import time
import jwt
import datetime
from typing import Optional
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
                f'LiveKit credentials not properly configured. '
                f'URL: {"✓" if self.url else "✗"}, '
                f'API_KEY: {"✓" if self.api_key else "✗"}, '
                f'API_SECRET: {"✓" if self.api_secret else "✗"}'
            )
        
        print(f'LiveKit initialized with URL: {self.url}')
    
    def generate_token(self, room_name: str, participant_name: str, is_host: bool = False) -> str:
        """Generate a LiveKit access token using direct JWT creation"""
        try:
            # Token expiration time (24 hours from now)
            now = datetime.datetime.now(datetime.timezone.utc)
            exp = now + datetime.timedelta(hours=24)
            
            # Create video grants
            video_grants = {
                'roomJoin': True,
                'room': room_name,
                'canPublish': True,
                'canSubscribe': True,
                'canPublishData': True
            }
            
            # Add host permissions
            if is_host:
                video_grants['roomAdmin'] = True
                video_grants['roomRecord'] = True
            
            # JWT payload
            payload = {
                'iss': self.api_key,  # issuer
                'sub': participant_name,  # subject (participant identity)
                'iat': int(now.timestamp()),  # issued at
                'exp': int(exp.timestamp()),  # expiration
                'nbf': int(now.timestamp()),  # not before
                'name': participant_name,
                'video': video_grants
            }
            
            # Generate JWT token
            token = jwt.encode(payload, self.api_secret, algorithm='HS256')
            
            print(f'Generated token for {participant_name} in room {room_name} (host: {is_host})')
            return token
            
        except Exception as e:
            print(f'Error generating token: {str(e)}')
            raise ValueError(f'Failed to generate LiveKit token: {str(e)}')
    
    def get_room_name(self, meeting_id: str) -> str:
        """Convert meeting ID to LiveKit room name"""
        # Ensure room name is valid (alphanumeric and hyphens only)
        room_name = f'meeting-{meeting_id}'.lower()
        room_name = ''.join(c for c in room_name if c.isalnum() or c in ['-', '_'])
        return room_name
    
    def validate_credentials(self) -> bool:
        """Validate that LiveKit credentials are properly configured"""
        try:
            # Try to create a test token
            test_payload = {
                'iss': self.api_key,
                'sub': 'test',
                'iat': int(time.time()),
                'exp': int(time.time()) + 60,
                'video': {'roomJoin': True, 'room': 'test'}
            }
            
            jwt.encode(test_payload, self.api_secret, algorithm='HS256')
            return True
        except Exception as e:
            print(f'LiveKit credentials validation failed: {str(e)}')
            return False