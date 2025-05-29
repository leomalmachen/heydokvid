#!/usr/bin/env python3
"""
Test script for enhanced Heydok Video API
Tests the improved LiveKit integration, security, and recording functionality
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
import sys


class HeydokVideoAPITester:
    """Test suite for Heydok Video API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_health_check(self):
        """Test health check endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("status") in ["healthy", "degraded"] and
                    "services" in data
                )
                
                self.log_test(
                    "Health Check",
                    success,
                    f"Status: {data.get('status')}, Services: {data.get('services', {})}"
                )
                
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
    
    async def test_create_meeting(self) -> Dict[str, Any]:
        """Test meeting creation with enhanced features"""
        try:
            payload = {
                "name": "Test Meeting - Enhanced API",
                "max_participants": 5,
                "enable_recording": True,
                "enable_chat": True,
                "enable_screen_share": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/meetings/create",
                json=payload
            ) as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("success") is True and
                    "meeting_id" in data and
                    "expires_at" in data
                )
                
                self.log_test(
                    "Create Meeting (Enhanced)",
                    success,
                    f"Meeting ID: {data.get('meeting_id')}, Expires: {data.get('expires_at')}"
                )
                
                return data if success else {}
                
        except Exception as e:
            self.log_test("Create Meeting (Enhanced)", False, f"Error: {str(e)}")
            return {}
    
    async def test_meeting_info(self, meeting_id: str):
        """Test getting meeting information"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/meetings/{meeting_id}/info"
            ) as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("exists") is True and
                    "num_participants" in data
                )
                
                self.log_test(
                    "Get Meeting Info",
                    success,
                    f"Participants: {data.get('num_participants')}, Full: {data.get('is_full')}"
                )
                
        except Exception as e:
            self.log_test("Get Meeting Info", False, f"Error: {str(e)}")
    
    async def test_join_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Test joining meeting with role-based permissions"""
        try:
            payload = {
                "user_name": "Dr. Test Physician",
                "user_role": "physician",
                "enable_video": True,
                "enable_audio": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/meetings/{meeting_id}/join",
                json=payload
            ) as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("success") is True and
                    "token" in data and
                    "permissions" in data
                )
                
                permissions = data.get("permissions", {})
                self.log_test(
                    "Join Meeting (Physician)",
                    success,
                    f"Token length: {len(data.get('token', ''))}, Admin: {permissions.get('is_admin')}"
                )
                
                return data if success else {}
                
        except Exception as e:
            self.log_test("Join Meeting (Physician)", False, f"Error: {str(e)}")
            return {}
    
    async def test_join_meeting_patient(self, meeting_id: str):
        """Test joining meeting as patient"""
        try:
            payload = {
                "user_name": "Test Patient",
                "user_role": "patient",
                "enable_video": True,
                "enable_audio": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/meetings/{meeting_id}/join",
                json=payload
            ) as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("success") is True and
                    "permissions" in data
                )
                
                permissions = data.get("permissions", {})
                self.log_test(
                    "Join Meeting (Patient)",
                    success,
                    f"Admin: {permissions.get('is_admin')}, Can publish data: {permissions.get('can_publish_data')}"
                )
                
        except Exception as e:
            self.log_test("Join Meeting (Patient)", False, f"Error: {str(e)}")
    
    async def test_token_validation(self, meeting_id: str, token: str):
        """Test token validation"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/meetings/{meeting_id}/validate-token",
                json={"token": token}
            ) as response:
                data = await response.json()
                
                success = (
                    response.status == 200 and
                    data.get("valid") is True and
                    data.get("room_name") == meeting_id
                )
                
                self.log_test(
                    "Token Validation",
                    success,
                    f"Valid: {data.get('valid')}, Room: {data.get('room_name')}"
                )
                
        except Exception as e:
            self.log_test("Token Validation", False, f"Error: {str(e)}")
    
    async def test_recording_endpoints(self, meeting_id: str):
        """Test recording functionality"""
        try:
            # Test start recording
            payload = {
                "meeting_id": meeting_id,
                "consent_participants": ["dr_test_physician", "test_patient"],
                "audio_only": False,
                "include_chat": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/recordings/start",
                json=payload
            ) as response:
                
                # Recording might fail if no authenticated user, but we test the endpoint
                success = response.status in [200, 401, 403]  # Expected responses
                
                if response.status == 200:
                    data = await response.json()
                    details = f"Recording ID: {data.get('recording_id')}"
                elif response.status == 401:
                    details = "Authentication required (expected)"
                else:
                    details = f"Status: {response.status}"
                
                self.log_test("Recording Start Endpoint", success, details)
                
        except Exception as e:
            self.log_test("Recording Start Endpoint", False, f"Error: {str(e)}")
        
        try:
            # Test list recordings
            async with self.session.get(
                f"{self.base_url}/api/v1/recordings/"
            ) as response:
                
                success = response.status in [200, 401]  # Expected responses
                details = f"Status: {response.status}"
                
                if response.status == 200:
                    data = await response.json()
                    details = f"Total recordings: {data.get('total_count', 0)}"
                
                self.log_test("Recording List Endpoint", success, details)
                
        except Exception as e:
            self.log_test("Recording List Endpoint", False, f"Error: {str(e)}")
    
    async def test_rate_limiting(self, meeting_id: str):
        """Test rate limiting functionality"""
        try:
            # Make multiple rapid requests
            tasks = []
            for i in range(15):  # Exceed the 10 calls per minute limit
                task = self.session.get(f"{self.base_url}/api/v1/meetings/{meeting_id}/exists")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any requests were rate limited (429 status)
            rate_limited = False
            for response in responses:
                if hasattr(response, 'status') and response.status == 429:
                    rate_limited = True
                    break
            
            self.log_test(
                "Rate Limiting",
                rate_limited,
                "Rate limiting triggered" if rate_limited else "No rate limiting detected"
            )
            
            # Close all responses
            for response in responses:
                if hasattr(response, 'close'):
                    response.close()
                    
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Error: {str(e)}")
    
    async def test_security_headers(self):
        """Test security headers"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                headers = response.headers
                
                required_headers = [
                    "X-Request-ID",
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "Strict-Transport-Security"
                ]
                
                missing_headers = [h for h in required_headers if h not in headers]
                success = len(missing_headers) == 0
                
                self.log_test(
                    "Security Headers",
                    success,
                    f"Missing: {missing_headers}" if missing_headers else "All headers present"
                )
                
        except Exception as e:
            self.log_test("Security Headers", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Heydok Video API Enhanced Test Suite")
        print("=" * 60)
        
        # Basic functionality tests
        await self.test_health_check()
        await self.test_security_headers()
        
        # Meeting functionality tests
        meeting_data = await self.test_create_meeting()
        
        if meeting_data and meeting_data.get("meeting_id"):
            meeting_id = meeting_data["meeting_id"]
            
            await self.test_meeting_info(meeting_id)
            
            # Join tests
            physician_data = await self.test_join_meeting(meeting_id)
            await self.test_join_meeting_patient(meeting_id)
            
            # Token validation
            if physician_data and physician_data.get("token"):
                await self.test_token_validation(meeting_id, physician_data["token"])
            
            # Recording tests
            await self.test_recording_endpoints(meeting_id)
            
            # Rate limiting test
            await self.test_rate_limiting(meeting_id)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed_tests == total_tests


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Heydok Video API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    async with HeydokVideoAPITester(args.url) as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! API is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Please check the API implementation.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 