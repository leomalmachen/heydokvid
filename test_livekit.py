#!/usr/bin/env python3
"""
Test script to verify LiveKit configuration and token generation
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_livekit_config():
    """Test LiveKit configuration"""
    print("Testing LiveKit Configuration...")
    print("=" * 50)
    
    # Check environment variables
    livekit_url = os.getenv('LIVEKIT_URL')
    livekit_api_key = os.getenv('LIVEKIT_API_KEY')
    livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')
    
    print(f"LIVEKIT_URL: {'✓' if livekit_url else '✗'} {livekit_url if livekit_url else 'Not set'}")
    print(f"LIVEKIT_API_KEY: {'✓' if livekit_api_key else '✗'} {livekit_api_key[:10] + '...' if livekit_api_key else 'Not set'}")
    print(f"LIVEKIT_API_SECRET: {'✓' if livekit_api_secret else '✗'} {'Set' if livekit_api_secret else 'Not set'}")
    
    if not all([livekit_url, livekit_api_key, livekit_api_secret]):
        print("\n❌ LiveKit configuration incomplete!")
        print("Please set all required environment variables:")
        print("- LIVEKIT_URL")
        print("- LIVEKIT_API_KEY") 
        print("- LIVEKIT_API_SECRET")
        return False
    
    print("\n✅ Environment variables are set")
    
    # Test LiveKit client
    try:
        from livekit_client import LiveKitClient
        
        print("\nTesting LiveKit client...")
        client = LiveKitClient()
        
        # Test credential validation
        if client.validate_credentials():
            print("✅ LiveKit credentials are valid")
        else:
            print("❌ LiveKit credentials validation failed")
            return False
            
        # Test token generation
        print("\nTesting token generation...")
        test_room = "test-room-123"
        test_participant = "test-user"
        
        token = client.generate_token(
            room_name=test_room,
            participant_name=test_participant,
            is_host=True
        )
        
        if token:
            print(f"✅ Token generated successfully (length: {len(token)})")
            print(f"Token preview: {token[:50]}...")
        else:
            print("❌ Token generation failed")
            return False
            
        print("\n🎉 All LiveKit tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import LiveKit client: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ LiveKit test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\nTesting Dependencies...")
    print("=" * 50)
    
    required_packages = [
        ('livekit', 'livekit'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ All dependencies are installed")
        return True

if __name__ == "__main__":
    print("LiveKit Configuration Test")
    print("=" * 50)
    
    deps_ok = test_dependencies()
    if not deps_ok:
        sys.exit(1)
    
    config_ok = test_livekit_config()
    if not config_ok:
        sys.exit(1)
    
    print("\n🎉 All tests passed! LiveKit is properly configured.") 