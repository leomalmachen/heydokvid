#!/bin/bash

echo "Starting Heydok Video Backend Development Server..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables for development
export DEBUG=True
export ENVIRONMENT=development
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
export LIVEKIT_URL=ws://localhost:7880
export FRONTEND_URL=http://localhost:3000

# Start the server
echo ""
echo "Starting FastAPI server..."
echo "API Documentation: http://localhost:8000/api/docs"
echo "Health Check: http://localhost:8000/health"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 