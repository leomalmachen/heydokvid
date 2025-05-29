#!/usr/bin/env python3
"""
Test script for the video meeting system
Tests the complete flow: create meeting -> join meeting -> verify functionality
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_NAME = "Test User"


async def test_create_meeting():
    """Test meeting creation"""
    print("🔄 Testing meeting creation...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Create a new meeting
            async with session.post(
                f"{API_BASE_URL}/api/v1/meetings/create",
                json={"name": "Test Meeting"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Meeting created successfully!")
                    print(f"   Meeting ID: {data['meeting_id']}")
                    print(f"   Meeting URL: {data['meeting_url']}")
                    print(f"   Created at: {data['created_at']}")
                    return data['meeting_id']
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create meeting: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating meeting: {e}")
            return None


async def test_meeting_info(meeting_id):
    """Test getting meeting information"""
    print(f"🔄 Testing meeting info for {meeting_id}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/info"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Meeting info retrieved successfully!")
                    print(f"   Status: {data['status']}")
                    print(f"   Meeting URL: {data['meeting_url']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get meeting info: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error getting meeting info: {e}")
            return False


async def test_meeting_exists(meeting_id):
    """Test checking if meeting exists"""
    print(f"🔄 Testing meeting exists check for {meeting_id}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/exists"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Meeting exists check successful!")
                    print(f"   Exists: {data['exists']}")
                    print(f"   Status: {data['status']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Meeting exists check failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error checking meeting exists: {e}")
            return False


async def test_join_meeting(meeting_id):
    """Test joining a meeting"""
    print(f"🔄 Testing joining meeting {meeting_id}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/meetings/{meeting_id}/join",
                json={"display_name": TEST_USER_NAME},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Successfully joined meeting!")
                    print(f"   Participant ID: {data['participant_id']}")
                    print(f"   LiveKit URL: {data['livekit_url']}")
                    print(f"   Token length: {len(data['token'])} characters")
                    print(f"   Token preview: {data['token'][:50]}...")
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to join meeting: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error joining meeting: {e}")
            return None


async def test_frontend_route(meeting_id):
    """Test frontend meeting route"""
    print(f"🔄 Testing frontend route for {meeting_id}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{API_BASE_URL}/meeting/{meeting_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Frontend route accessible!")
                    print(f"   Meeting ID: {data['meeting_id']}")
                    print(f"   Available endpoints: {list(data['api_endpoints'].keys())}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Frontend route failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error accessing frontend route: {e}")
            return False


async def test_health_check():
    """Test health check endpoint"""
    print("🔄 Testing health check...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed!")
                    print(f"   Status: {data['status']}")
                    print(f"   Version: {data['version']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Health check failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in health check: {e}")
            return False


async def test_invalid_meeting():
    """Test behavior with invalid meeting ID"""
    print("🔄 Testing invalid meeting ID...")
    
    invalid_id = "invalid-meeting-id"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/meetings/{invalid_id}/join",
                json={"display_name": TEST_USER_NAME},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 404:
                    print(f"✅ Correctly rejected invalid meeting ID!")
                    return True
                else:
                    print(f"❌ Unexpected response for invalid meeting: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error testing invalid meeting: {e}")
            return False


async def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting Video Meeting System Tests")
    print("=" * 50)
    
    # Test health check first
    if not await test_health_check():
        print("❌ Health check failed - server may not be running")
        return False
    
    print()
    
    # Test meeting creation
    meeting_id = await test_create_meeting()
    if not meeting_id:
        print("❌ Cannot continue tests without a valid meeting")
        return False
    
    print()
    
    # Test meeting info
    if not await test_meeting_info(meeting_id):
        print("❌ Meeting info test failed")
        return False
    
    print()
    
    # Test meeting exists
    if not await test_meeting_exists(meeting_id):
        print("❌ Meeting exists test failed")
        return False
    
    print()
    
    # Test frontend route
    if not await test_frontend_route(meeting_id):
        print("❌ Frontend route test failed")
        return False
    
    print()
    
    # Test joining meeting
    join_data = await test_join_meeting(meeting_id)
    if not join_data:
        print("❌ Join meeting test failed")
        return False
    
    print()
    
    # Test invalid meeting
    if not await test_invalid_meeting():
        print("❌ Invalid meeting test failed")
        return False
    
    print()
    print("=" * 50)
    print("🎉 All tests passed successfully!")
    print()
    print("📋 Test Summary:")
    print(f"   ✅ Meeting created: {meeting_id}")
    print(f"   ✅ Meeting info retrieved")
    print(f"   ✅ Meeting exists check passed")
    print(f"   ✅ Frontend route accessible")
    print(f"   ✅ Meeting join successful")
    print(f"   ✅ Invalid meeting handling correct")
    print()
    print("🔗 Test Meeting URL:")
    print(f"   {API_BASE_URL}/meeting/{meeting_id}")
    print()
    print("🎯 Next Steps:")
    print("   1. Open the meeting URL in a browser")
    print("   2. Test with multiple participants")
    print("   3. Verify video/audio functionality")
    
    return True


if __name__ == "__main__":
    print("Video Meeting System Test Suite")
    print(f"Testing against: {API_BASE_URL}")
    print()
    
    try:
        success = asyncio.run(run_all_tests())
        if success:
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        sys.exit(1) 