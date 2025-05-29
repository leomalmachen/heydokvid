#!/bin/bash

echo "Starting Video Meeting Platform..."
echo "================================="

# Kill any existing processes on the ports
echo "Cleaning up existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null

# Start Backend
echo "Starting Backend on port 8001..."
cd backend
python -m uvicorn simple_meetings_api:app --reload --port 8001 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✓ Backend is running on http://localhost:8001"
else
    echo "✗ Backend failed to start"
    exit 1
fi

# Start Frontend
echo "Starting Frontend on port 3001..."
cd frontend/heydok-video-frontend
PORT=3001 npm start &
FRONTEND_PID=$!
cd ../..

echo ""
echo "================================="
echo "Video Meeting Platform is starting!"
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================="

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 