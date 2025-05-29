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

# LiveKit Configuration
export LIVEKIT_API_KEY=APIM4pxPvXu6uF4
export LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
export LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud

# Frontend URL
export FRONTEND_URL=http://localhost:3000

# Start the server
echo ""
echo "Starting FastAPI server..."
echo "API Documentation: http://localhost:8000/api/docs"
echo "Health Check: http://localhost:8000/health"
echo "LiveKit URL: wss://malmachen-8s6xtzpq.livekit.cloud"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 