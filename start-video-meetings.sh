#!/bin/bash

# Video Meeting System Startup Script
echo "🎥 Starting Video Meeting System..."

# Set environment variables for LiveKit Cloud
export LIVEKIT_API_KEY="APIwkvkVSaRyTE3"
export LIVEKIT_API_SECRET="7FVh4h09qkZyejvgtV4Mc5Yo6uNgaMNVofxvCQBnRgf"
export LIVEKIT_URL="wss://google-meet-replacer-fcw5apmd.livekit.cloud"
export PORT=8000
export HOST=0.0.0.0
export ENVIRONMENT=development

# Kill any existing processes on port 8000
echo "Stopping any existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-multipart==0.0.6
pip install livekit==0.1.2
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
pip install pyjwt==2.8.0
pip install pydantic==2.4.2
pip install pydantic-settings==2.1.0
pip install httpx==0.25.2
pip install aiohttp==3.9.1
pip install python-dotenv==1.0.0
pip install fastapi-cors==0.0.6
pip install structlog==23.2.0

echo ""
echo "✅ Video Meeting System is starting..."
echo "📱 Frontend: http://localhost:8000"
echo "🎥 Create Meeting: http://localhost:8000"
echo "🔗 Join Meeting: http://localhost:8000/meeting/{meeting-id}"
echo "🔧 API Health: http://localhost:8000/health"
echo ""
echo "🚀 Features:"
echo "   - Create new meetings with shareable links"
echo "   - Join existing meetings by ID"
echo "   - Video and audio communication via LiveKit Cloud"
echo "   - No registration required"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
python backend/main.py 