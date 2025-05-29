"""
Grok client for video meetings
"""
from typing import Optional, Dict
import os
import requests

class GrokClient:
    def __init__(self):
        self.api_url = os.getenv('GROK_API_URL', 'https://f2f9-217-138-216-222.ngrok-free.app/api')
        self.api_key = os.getenv('GROK_API_KEY', '')

    async def create_room(self, room_name: str, max_participants: int = 50, empty_timeout: int = 3600) -> Dict:
        """Create a new Grok video room"""
        response = requests.post(
            f"{self.api_url}/rooms",
            json={
                "name": room_name,
                "maxParticipants": max_participants,
                "emptyTimeout": empty_timeout
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_room(self, room_name: str) -> Optional[Dict]:
        """Get room details"""
        try:
            response = requests.get(
                f"{self.api_url}/rooms/{room_name}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def generate_token(self, room_name: str, identity: str, user_role: str = "participant", metadata: Dict = None) -> str:
        """Generate access token for a room"""
        response = requests.post(
            f"{self.api_url}/tokens",
            json={
                "roomName": room_name,
                "identity": identity,
                "role": user_role,
                "metadata": metadata or {}
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()["token"]

# Create a singleton instance
grok_client = GrokClient() 