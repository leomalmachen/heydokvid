#!/bin/bash

echo "🚀 Starting Video Meeting Platform..."
echo ""

# Check if LiveKit is running
if ! curl -s http://localhost:7880/health > /dev/null 2>&1; then
    echo "⚠️  LiveKit is not running!"
    echo ""
    echo "Please start LiveKit first with one of these commands:"
    echo ""
    echo "Option 1 (Docker):"
    echo "docker run -d -p 7880:7880 -p 7881:7881 -p 7882:7882/udp -e LIVEKIT_KEYS=\"devkey: secret\" livekit/livekit-server --dev --node-ip=127.0.0.1"
    echo ""
    echo "Option 2 (Binary):"
    echo "livekit-server --dev --node-ip=127.0.0.1"
    echo ""
    exit 1
fi

echo "✅ LiveKit is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Frontend URL
FRONTEND_URL=http://localhost:8001

# Backend Port
PORT=8001
EOF
    echo "✅ .env file created"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

# Start the backend
echo "🎬 Starting Video Meeting Backend..."
echo "📍 Access the application at: http://localhost:8001"
echo ""
echo "To test with multiple participants:"
echo "1. Open http://localhost:8001 and start a meeting"
echo "2. Copy the meeting URL and open it in another browser/tab"
echo "3. Both participants will see each other"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python -m uvicorn simple_meetings_api:app --reload --port 8001 --host 0.0.0.0 