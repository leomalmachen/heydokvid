#!/bin/bash

echo "🚀 Starting Simple Meet with Public Access..."
echo ""

# Function to extract ngrok URL
get_ngrok_url() {
    local port=$1
    sleep 2
    curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" | head -1
}

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "node.*simple-meet"
pkill -f "ngrok"
sleep 2

# Install dependencies if needed
if [ ! -d "backend/node_modules" ]; then
    echo "📦 Installing backend dependencies..."
    cd backend && npm install && cd ..
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend
echo "🖥️  Starting backend server..."
cd backend
PORT=5001 npm start &
BACKEND_PID=$!
cd ..
sleep 3

# Start ngrok for backend
echo "🌐 Creating public URL for backend..."
ngrok http 5001 --log=stdout > /tmp/ngrok-backend.log 2>&1 &
NGROK_BACKEND_PID=$!
sleep 5

# Get backend URL
BACKEND_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" | head -1)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Failed to get ngrok URL for backend"
    kill $BACKEND_PID $NGROK_BACKEND_PID
    exit 1
fi

echo "✅ Backend is publicly accessible at: $BACKEND_URL"

# Create .env file for frontend
echo "REACT_APP_SOCKET_SERVER=$BACKEND_URL" > frontend/.env

# Start frontend with the backend URL
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3

# Start ngrok for frontend
echo "🌐 Creating public URL for frontend..."
ngrok http 3000 --log=stdout > /tmp/ngrok-frontend.log 2>&1 &
NGROK_FRONTEND_PID=$!
sleep 5

# Get frontend URL
FRONTEND_URL=$(curl -s http://localhost:4041/api/tunnels | grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" | head -1)

if [ -z "$FRONTEND_URL" ]; then
    # Try alternative port
    FRONTEND_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" | tail -1)
fi

echo ""
echo "🎉 Simple Meet is now publicly accessible!"
echo "================================================"
echo "📱 Share this link: $FRONTEND_URL"
echo "================================================"
echo ""
echo "Backend API: $BACKEND_URL"
echo "Local Frontend: http://localhost:3000"
echo "Local Backend: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID $NGROK_BACKEND_PID $NGROK_FRONTEND_PID 2>/dev/null
    rm -f frontend/.env
    exit
}

trap cleanup INT

# Wait
wait 