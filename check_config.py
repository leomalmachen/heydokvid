#!/usr/bin/env python3
"""
LiveKit Configuration Checker
Überprüft ob alle notwendigen Umgebungsvariablen gesetzt sind
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_config():
    """Check if all required environment variables are set"""
    print("=== LiveKit Configuration Check ===\n")
    
    required_vars = {
        'LIVEKIT_URL': 'LiveKit Server URL (z.B. wss://your-livekit-server.com)',
        'LIVEKIT_API_KEY': 'LiveKit API Key',
        'LIVEKIT_API_SECRET': 'LiveKit API Secret'
    }
    
    optional_vars = {
        'APP_URL': 'Application URL (für Heroku)',
        'HEROKU_APP_NAME': 'Heroku App Name',
        'PORT': 'Server Port'
    }
    
    all_good = True
    
    print("Required Variables:")
    print("-" * 50)
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if 'SECRET' in var or 'KEY' in var:
                masked_value = value[:4] + '***' + value[-4:] if len(value) > 8 else '***'
                print(f"✓ {var}: {masked_value}")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET ({description})")
            all_good = False
    
    print("\nOptional Variables:")
    print("-" * 50)
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: Not set ({description})")
    
    # Test LiveKit client initialization
    print("\nLiveKit Client Test:")
    print("-" * 50)
    try:
        from livekit_client import LiveKitClient
        client = LiveKitClient()
        if client.validate_credentials():
            print("✓ LiveKit client initialized successfully")
            print(f"✓ LiveKit URL: {client.url}")
            
            # Try to generate a test token
            try:
                token = client.generate_token("test-room", "test-user", True)
                print("✓ Test token generation successful")
            except Exception as e:
                print(f"✗ Token generation failed: {e}")
                all_good = False
        else:
            print("✗ LiveKit credentials validation failed")
            all_good = False
    except Exception as e:
        print(f"✗ LiveKit client initialization failed: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ All checks passed! Your configuration looks good.")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nHinweise:")
        print("1. Stelle sicher, dass alle LIVEKIT_* Variablen in Heroku gesetzt sind")
        print("2. Überprüfe ob dein LiveKit Server läuft und erreichbar ist")
        print("3. Verwende 'heroku config:set VARIABLE_NAME=value' um Variablen zu setzen")
    
    return all_good

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1) 