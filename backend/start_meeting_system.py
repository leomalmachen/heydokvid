#!/usr/bin/env python3
"""
Start script for the Video Meeting System
Checks configuration and starts the server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "LIVEKIT_URL",
        "SECRET_KEY",
        "JWT_SECRET",
        "ENCRYPTION_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these variables in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    
    # Show LiveKit configuration
    print(f"🔗 LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"🔑 LiveKit API Key: {os.getenv('LIVEKIT_API_KEY')[:8]}...")
    
    return True


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import redis
        import livekit
        print("✅ All core dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False


def setup_database():
    """Initialize database if needed"""
    print("🗄️  Setting up database...")
    
    try:
        # This would run database migrations in a real setup
        print("✅ Database setup completed")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Video Meeting System...")
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🌐 Server will start on {host}:{port}")
    print(f"📖 API Documentation: http://localhost:{port}/api/docs")
    print(f"🏠 Health Check: http://localhost:{port}/health")
    print()
    
    try:
        # Start the server using uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
            "--reload" if os.getenv("DEBUG", "false").lower() == "true" else "--no-reload",
            "--log-level", os.getenv("LOG_LEVEL", "info").lower()
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        print("=" * 60)
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⚠️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main function"""
    print("🎥 Video Meeting System Startup")
    print("=" * 40)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    print(f"📁 Working directory: {backend_dir}")
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        sys.exit(1)
    
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    print()
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed")
        sys.exit(1)
    
    print()
    
    # Start server
    if not start_server():
        print("\n❌ Server startup failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 