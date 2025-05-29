#!/bin/bash

# Heydok Video - Local Development Setup (No Docker Required)
# This script starts the backend API locally for development

set -e  # Exit on any error

echo "🚀 Starting Heydok Video Local Development..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

print_success "✅ Python 3 found: $(python3 --version)"

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
elif [ -f "requirements-production.txt" ]; then
    pip install -q -r requirements-production.txt
else
    print_error "No requirements file found!"
    exit 1
fi

# Set environment variables for local development
export ENVIRONMENT=development
export DEBUG=true
export PORT=8002
export LIVEKIT_API_KEY=APIM4pxPvXu6uF4
export LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
export LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080,http://localhost:8002"

print_status "Environment variables set for development"

# Function to cleanup background processes
cleanup() {
    print_status "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start backend server
print_status "🔧 Starting backend API on port 8002..."

# Check which backend file to use
if [ -f "simple_meetings_api.py" ]; then
    python simple_meetings_api.py &
    BACKEND_PID=$!
elif [ -f "main.py" ]; then
    python main.py &
    BACKEND_PID=$!
else
    print_error "No backend main file found!"
    exit 1
fi

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    print_error "❌ Failed to start backend server"
    exit 1
fi

print_success "✅ Backend API started (PID: $BACKEND_PID)"

# Navigate back to root directory
cd ..

echo ""
print_success "🎉 Local development system is ready!"
echo ""
echo "📋 Service URLs:"
echo "   🚀 Backend API:       http://localhost:8002"
echo "   📖 API Documentation: http://localhost:8002/docs"
echo "   🌐 Meeting Interface: http://localhost:8002/meeting.html"
echo "   🏠 Home Page:         http://localhost:8002/"
echo ""
echo "🎥 Using LiveKit Cloud Service:"
echo "   🔗 LiveKit URL:       wss://malmachen-8s6xtzpq.livekit.cloud"
echo ""
echo "🧪 Quick Test:"
echo "   Create meeting:       curl -X POST http://localhost:8002/api/v1/meetings/create"
echo "   Open browser:         open http://localhost:8002/"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo ""

# Wait for user to stop the script and show logs
wait $BACKEND_PID 