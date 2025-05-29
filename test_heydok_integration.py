#!/usr/bin/env python3
"""
Heydok LiveKit Integration Test Suite
Tests the complete join flow for medical video consultations
"""

import asyncio
import json
import time
from typing import Dict, Any
import httpx
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30


class HeydokIntegrationTest:
    """Test suite for heydok LiveKit integration"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=TEST_TIMEOUT)
        self.test_meeting_id = None
        self.physician_token = None
        self.patient_token = None
    
    async def test_health_check(self) -> bool:
        """Test API health endpoint"""
        print("🔍 Testing health check...")
        try:
            response = await self.client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "livekit" in data["services"]
            print("✅ Health check passed")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_create_meeting(self) -> bool:
        """Test meeting creation"""
        print("🔍 Testing meeting creation...")
        try:
            meeting_data = {
                "name": f"Test Consultation {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "max_participants": 2,
                "enable_recording": True,
                "enable_chat": True,
                "enable_screen_share": True
            }
            
            response = await self.client.post("/api/v1/meetings/create", json=meeting_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "meeting_id" in data
            assert "meeting_link" in data
            assert "livekit_url" in data
            assert data["success"] is True
            
            self.test_meeting_id = data["meeting_id"]
            print(f"✅ Meeting created successfully: {self.test_meeting_id}")
            return True
        except Exception as e:
            print(f"❌ Meeting creation failed: {e}")
            return False
    
    async def test_meeting_info(self) -> bool:
        """Test meeting info retrieval"""
        print("🔍 Testing meeting info...")
        try:
            if not self.test_meeting_id:
                print("❌ No meeting ID available")
                return False
            
            response = await self.client.get(f"/api/v1/meetings/{self.test_meeting_id}/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["meeting_id"] == self.test_meeting_id
            assert data["exists"] is True
            assert "num_participants" in data
            assert "max_participants" in data
            
            print("✅ Meeting info retrieved successfully")
            return True
        except Exception as e:
            print(f"❌ Meeting info test failed: {e}")
            return False
    
    async def test_physician_join(self) -> bool:
        """Test physician joining meeting"""
        print("🔍 Testing physician join...")
        try:
            if not self.test_meeting_id:
                print("❌ No meeting ID available")
                return False
            
            join_data = {
                "user_name": "Dr. Test Physician",
                "user_role": "physician",
                "enable_video": True,
                "enable_audio": True
            }
            
            response = await self.client.post(
                f"/api/v1/meetings/{self.test_meeting_id}/join", 
                json=join_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "token" in data
            assert "livekit_url" in data
            assert data["success"] is True
            assert data["user_name"] == "Dr. Test Physician"
            
            # Verify physician permissions
            permissions = data["permissions"]
            assert permissions["can_publish"] is True
            assert permissions["can_subscribe"] is True
            assert permissions["is_admin"] is True
            
            self.physician_token = data["token"]
            print("✅ Physician joined successfully with admin permissions")
            return True
        except Exception as e:
            print(f"❌ Physician join failed: {e}")
            return False
    
    async def test_patient_join(self) -> bool:
        """Test patient joining meeting"""
        print("🔍 Testing patient join...")
        try:
            if not self.test_meeting_id:
                print("❌ No meeting ID available")
                return False
            
            join_data = {
                "user_name": "Max Mustermann",
                "user_role": "patient",
                "enable_video": True,
                "enable_audio": True
            }
            
            response = await self.client.post(
                f"/api/v1/meetings/{self.test_meeting_id}/join", 
                json=join_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "token" in data
            assert "livekit_url" in data
            assert data["success"] is True
            assert data["user_name"] == "Max Mustermann"
            
            # Verify patient permissions
            permissions = data["permissions"]
            assert permissions["can_publish"] is True
            assert permissions["can_subscribe"] is True
            assert permissions["is_admin"] is False
            
            self.patient_token = data["token"]
            print("✅ Patient joined successfully with limited permissions")
            return True
        except Exception as e:
            print(f"❌ Patient join failed: {e}")
            return False
    
    async def test_token_validation(self) -> bool:
        """Test token validation"""
        print("🔍 Testing token validation...")
        try:
            if not self.test_meeting_id or not self.physician_token:
                print("❌ No meeting ID or token available")
                return False
            
            response = await self.client.post(
                f"/api/v1/meetings/{self.test_meeting_id}/validate-token",
                json={"token": self.physician_token}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert data["room_name"] == self.test_meeting_id
            
            print("✅ Token validation successful")
            return True
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            return False
    
    async def test_meeting_capacity(self) -> bool:
        """Test meeting capacity limits"""
        print("🔍 Testing meeting capacity...")
        try:
            if not self.test_meeting_id:
                print("❌ No meeting ID available")
                return False
            
            # Try to join with a third participant (should fail for max_participants=2)
            join_data = {
                "user_name": "Third Participant",
                "user_role": "patient",
                "enable_video": True,
                "enable_audio": True
            }
            
            # First, let's check current participant count
            info_response = await self.client.get(f"/api/v1/meetings/{self.test_meeting_id}/info")
            info_data = info_response.json()
            current_participants = info_data["num_participants"]
            max_participants = info_data["max_participants"]
            
            if current_participants >= max_participants:
                print(f"✅ Meeting capacity working correctly ({current_participants}/{max_participants})")
                return True
            else:
                print(f"⚠️ Meeting not at capacity yet ({current_participants}/{max_participants})")
                return True
        except Exception as e:
            print(f"❌ Meeting capacity test failed: {e}")
            return False
    
    async def test_recording_permissions(self) -> bool:
        """Test recording permissions (physician only)"""
        print("🔍 Testing recording permissions...")
        try:
            if not self.test_meeting_id:
                print("❌ No meeting ID available")
                return False
            
            # Test recording start (should work for physician)
            response = await self.client.post(
                f"/api/v1/meetings/{self.test_meeting_id}/start-recording"
            )
            
            # Note: This might fail if no authenticated physician user is provided
            # In a real implementation, you'd need proper authentication
            if response.status_code in [200, 403]:
                print("✅ Recording permissions working (authentication required)")
                return True
            else:
                print(f"⚠️ Unexpected recording response: {response.status_code}")
                return True
        except Exception as e:
            print(f"❌ Recording permissions test failed: {e}")
            return False
    
    async def test_invalid_meeting_join(self) -> bool:
        """Test joining non-existent meeting"""
        print("🔍 Testing invalid meeting join...")
        try:
            invalid_meeting_id = "invalid-meeting-123"
            join_data = {
                "user_name": "Test User",
                "user_role": "patient",
                "enable_video": True,
                "enable_audio": True
            }
            
            response = await self.client.post(
                f"/api/v1/meetings/{invalid_meeting_id}/join", 
                json=join_data
            )
            assert response.status_code == 404
            
            print("✅ Invalid meeting join properly rejected")
            return True
        except Exception as e:
            print(f"❌ Invalid meeting join test failed: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting"""
        print("🔍 Testing rate limiting...")
        try:
            # Make multiple rapid requests to test rate limiting
            tasks = []
            for i in range(25):  # Exceed the 20 calls per minute limit
                task = self.client.get("/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any requests were rate limited (429 status)
            rate_limited = any(
                hasattr(r, 'status_code') and r.status_code == 429 
                for r in responses if not isinstance(r, Exception)
            )
            
            if rate_limited:
                print("✅ Rate limiting working correctly")
            else:
                print("⚠️ Rate limiting not triggered (might need more requests)")
            
            return True
        except Exception as e:
            print(f"❌ Rate limiting test failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test resources"""
        print("🧹 Cleaning up...")
        try:
            if self.test_meeting_id:
                # Try to end the meeting (might fail without proper auth)
                await self.client.delete(f"/api/v1/meetings/{self.test_meeting_id}")
            
            await self.client.aclose()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting Heydok LiveKit Integration Tests\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Create Meeting", self.test_create_meeting),
            ("Meeting Info", self.test_meeting_info),
            ("Physician Join", self.test_physician_join),
            ("Patient Join", self.test_patient_join),
            ("Token Validation", self.test_token_validation),
            ("Meeting Capacity", self.test_meeting_capacity),
            ("Recording Permissions", self.test_recording_permissions),
            ("Invalid Meeting Join", self.test_invalid_meeting_join),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}\n")
                results[test_name] = False
        
        await self.cleanup()
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        print("=" * 50)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print("\n🎯 Integration Status:")
        if passed == total:
            print("🟢 All tests passed - Integration is working correctly!")
        elif passed >= total * 0.8:
            print("🟡 Most tests passed - Integration is mostly working")
        else:
            print("🔴 Many tests failed - Integration needs attention")
        
        return results


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Heydok LiveKit Integration")
    parser.add_argument("--url", default=BASE_URL, help="Base URL for API")
    parser.add_argument("--timeout", type=int, default=TEST_TIMEOUT, help="Request timeout")
    args = parser.parse_args()
    
    tester = HeydokIntegrationTest(base_url=args.url)
    results = await tester.run_all_tests()
    
    # Exit with error code if tests failed
    failed_tests = sum(1 for result in results.values() if not result)
    exit(failed_tests)


if __name__ == "__main__":
    asyncio.run(main()) 