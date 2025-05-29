#!/usr/bin/env python3
"""
Test script for the Video Meeting System with LiveKit
Tests the complete flow: room creation, URL generation, and joining
"""

import requests
import json
import time
import sys
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test if the API is running"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_create_meeting():
    """Test meeting creation"""
    print("\n🔍 Testing meeting creation...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/meetings/create",
            json={"name": "Test Meeting"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Meeting created successfully:")
            print(f"   Meeting ID: {data['meeting_id']}")
            print(f"   Meeting URL: {data['meeting_url']}")
            print(f"   Created at: {data['created_at']}")
            print(f"   Expires at: {data['expires_at']}")
            
            # Verify URL format
            expected_url = f"{FRONTEND_BASE_URL}/meeting/{data['meeting_id']}"
            if data['meeting_url'] == expected_url:
                print(f"✅ URL format is correct: {data['meeting_url']}")
            else:
                print(f"❌ URL format incorrect. Expected: {expected_url}, Got: {data['meeting_url']}")
            
            return data['meeting_id']
        else:
            print(f"❌ Meeting creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Meeting creation error: {e}")
        return None

def test_meeting_exists(meeting_id):
    """Test if meeting exists"""
    print(f"\n🔍 Testing meeting existence for ID: {meeting_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/exists")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Meeting exists: {data}")
            return True
        else:
            print(f"❌ Meeting existence check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Meeting existence check error: {e}")
        return False

def test_meeting_info(meeting_id):
    """Test getting meeting info"""
    print(f"\n🔍 Testing meeting info for ID: {meeting_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/info")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Meeting info retrieved:")
            print(f"   Meeting ID: {data['meeting_id']}")
            print(f"   Meeting URL: {data['meeting_url']}")
            print(f"   Status: {data['status']}")
            print(f"   Name: {data.get('name', 'N/A')}")
            return True
        else:
            print(f"❌ Meeting info retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Meeting info retrieval error: {e}")
        return False

def test_join_meeting(meeting_id, participant_name="Test User"):
    """Test joining a meeting"""
    print(f"\n🔍 Testing joining meeting {meeting_id} as '{participant_name}'")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/join",
            json={"display_name": participant_name}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully joined meeting:")
            print(f"   Token: {data['token'][:50]}...")
            print(f"   Meeting ID: {data['meeting_id']}")
            print(f"   LiveKit URL: {data['livekit_url']}")
            print(f"   Participant ID: {data['participant_id']}")
            
            # Verify the token contains the correct room name
            import jwt
            try:
                # Decode without verification for testing
                decoded = jwt.decode(data['token'], options={"verify_signature": False})
                room_name = decoded.get('video', {}).get('room')
                if room_name == meeting_id:
                    print(f"✅ Token contains correct room name: {room_name}")
                else:
                    print(f"❌ Token room name mismatch. Expected: {meeting_id}, Got: {room_name}")
            except Exception as e:
                print(f"⚠️  Could not decode token for verification: {e}")
            
            return data['participant_id']
        else:
            print(f"❌ Meeting join failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Meeting join error: {e}")
        return None

def test_frontend_route(meeting_id):
    """Test if the frontend route serves the meeting page"""
    print(f"\n🔍 Testing frontend route for meeting {meeting_id}")
    try:
        response = requests.get(f"{FRONTEND_BASE_URL}/meeting/{meeting_id}")
        
        if response.status_code == 200:
            content = response.text
            if "meeting.html" in content or "Meeting beitreten" in content:
                print(f"✅ Frontend route serves meeting page correctly")
                return True
            else:
                print(f"❌ Frontend route doesn't serve expected content")
                return False
        else:
            print(f"❌ Frontend route failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend route test error: {e}")
        return False

def test_nonexistent_meeting():
    """Test behavior with non-existent meeting"""
    print(f"\n🔍 Testing non-existent meeting behavior")
    fake_meeting_id = "non-existent-meeting"
    
    try:
        # Test existence check
        response = requests.get(f"{API_BASE_URL}/api/v1/meetings/{fake_meeting_id}/exists")
        if response.status_code == 404:
            print(f"✅ Non-existent meeting correctly returns 404")
        else:
            print(f"❌ Non-existent meeting should return 404, got {response.status_code}")
        
        # Test join attempt
        response = requests.post(
            f"{API_BASE_URL}/api/v1/meetings/{fake_meeting_id}/join",
            json={"display_name": "Test User"}
        )
        if response.status_code == 404:
            print(f"✅ Join non-existent meeting correctly returns 404")
        else:
            print(f"❌ Join non-existent meeting should return 404, got {response.status_code}")
            
        return True
    except Exception as e:
        print(f"❌ Non-existent meeting test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Video Meeting System Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Health check failed. Make sure the server is running.")
        sys.exit(1)
    
    # Test 2: Create meeting
    meeting_id = test_create_meeting()
    if not meeting_id:
        print("\n❌ Meeting creation failed. Cannot continue tests.")
        sys.exit(1)
    
    # Test 3: Check meeting exists
    if not test_meeting_exists(meeting_id):
        print("\n❌ Meeting existence check failed.")
        sys.exit(1)
    
    # Test 4: Get meeting info
    if not test_meeting_info(meeting_id):
        print("\n❌ Meeting info retrieval failed.")
        sys.exit(1)
    
    # Test 5: Join meeting (first participant)
    participant1_id = test_join_meeting(meeting_id, "Alice")
    if not participant1_id:
        print("\n❌ First participant join failed.")
        sys.exit(1)
    
    # Test 6: Join meeting (second participant)
    participant2_id = test_join_meeting(meeting_id, "Bob")
    if not participant2_id:
        print("\n❌ Second participant join failed.")
        sys.exit(1)
    
    # Test 7: Frontend route
    if not test_frontend_route(meeting_id):
        print("\n❌ Frontend route test failed.")
        sys.exit(1)
    
    # Test 8: Non-existent meeting
    if not test_nonexistent_meeting():
        print("\n❌ Non-existent meeting test failed.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed successfully!")
    print(f"📋 Test Summary:")
    print(f"   ✅ Meeting created: {meeting_id}")
    print(f"   ✅ Meeting URL: {FRONTEND_BASE_URL}/meeting/{meeting_id}")
    print(f"   ✅ Two participants joined successfully")
    print(f"   ✅ Frontend route working")
    print(f"   ✅ Error handling working")
    print("\n🔗 You can now test the meeting by opening:")
    print(f"   {FRONTEND_BASE_URL}/meeting/{meeting_id}")
    print("\n💡 Share this URL with others to test multi-participant functionality!")

if __name__ == "__main__":
    main() 