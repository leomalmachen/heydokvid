#!/usr/bin/env python3
"""
Test script for the Meeting API
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_meeting_api():
    """
    Test the meeting API endpoints
    """
    base_url = "http://localhost:8000/api/v1/meetings"
    
    async with httpx.AsyncClient() as client:
        print("=" * 50)
        print("Testing Meeting API")
        print("=" * 50)
        
        # 1. Create a meeting
        print("\n1. Creating a meeting...")
        response = await client.post(f"{base_url}/create")
        if response.status_code == 200:
            meeting_data = response.json()
            meeting_id = meeting_data["meeting_id"]
            print(f"✓ Meeting created successfully!")
            print(f"  Meeting ID: {meeting_id}")
            print(f"  Meeting Link: {meeting_data['meeting_link']}")
            print(f"  LiveKit URL: {meeting_data['livekit_url']}")
        else:
            print(f"✗ Failed to create meeting: {response.status_code}")
            print(f"  Response: {response.text}")
            return
        
        # 2. Check if meeting exists
        print(f"\n2. Checking if meeting {meeting_id} exists...")
        response = await client.get(f"{base_url}/{meeting_id}/exists")
        if response.status_code == 200:
            exists_data = response.json()
            print(f"✓ Meeting exists: {exists_data['exists']}")
        else:
            print(f"✗ Failed to check meeting: {response.status_code}")
        
        # 3. Get meeting info
        print(f"\n3. Getting meeting info...")
        response = await client.get(f"{base_url}/{meeting_id}/info")
        if response.status_code == 200:
            info_data = response.json()
            print(f"✓ Meeting info retrieved:")
            print(f"  Exists: {info_data['exists']}")
            print(f"  Participants: {info_data['num_participants']}")
            print(f"  Max Participants: {info_data['max_participants']}")
        else:
            print(f"✗ Failed to get meeting info: {response.status_code}")
        
        # 4. Join meeting as User 1
        print(f"\n4. Joining meeting as User 1...")
        join_data = {"user_name": "Test User 1"}
        response = await client.post(f"{base_url}/{meeting_id}/join", json=join_data)
        if response.status_code == 200:
            user1_data = response.json()
            print(f"✓ User 1 joined successfully!")
            print(f"  User ID: {user1_data['user_id']}")
            print(f"  Token: {user1_data['token'][:50]}...")
        else:
            print(f"✗ Failed to join meeting: {response.status_code}")
            print(f"  Response: {response.text}")
        
        # 5. Join meeting as User 2
        print(f"\n5. Joining meeting as User 2...")
        join_data = {"user_name": "Test User 2"}
        response = await client.post(f"{base_url}/{meeting_id}/join", json=join_data)
        if response.status_code == 200:
            user2_data = response.json()
            print(f"✓ User 2 joined successfully!")
            print(f"  User ID: {user2_data['user_id']}")
        else:
            print(f"✗ Failed to join meeting: {response.status_code}")
        
        # 6. List participants
        print(f"\n6. Listing participants...")
        response = await client.get(f"{base_url}/{meeting_id}/participants")
        if response.status_code == 200:
            participants_data = response.json()
            print(f"✓ Participants retrieved:")
            print(f"  Count: {participants_data['count']}")
            for p in participants_data['participants']:
                print(f"  - {p.get('name', p.get('identity'))}")
        else:
            print(f"✗ Failed to list participants: {response.status_code}")
        
        # 7. Test non-existent meeting
        print(f"\n7. Testing non-existent meeting...")
        fake_id = "xxx-xxxx-xxx"
        response = await client.get(f"{base_url}/{fake_id}/exists")
        if response.status_code == 200:
            exists_data = response.json()
            print(f"✓ Non-existent meeting check: exists={exists_data['exists']}")
        
        # 8. Delete meeting (optional)
        # print(f"\n8. Deleting meeting...")
        # response = await client.delete(f"{base_url}/{meeting_id}")
        # if response.status_code == 200:
        #     print(f"✓ Meeting deleted successfully!")
        # else:
        #     print(f"✗ Failed to delete meeting: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Test completed!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_meeting_api()) 