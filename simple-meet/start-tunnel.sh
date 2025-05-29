#!/bin/bash

echo "🚀 Starting Simple Meet with Public Access (localtunnel)..."
echo ""

# Check if localtunnel is installed
if ! command -v lt &> /dev/null; then
    echo "📦 Installing localtunnel..."
    npm install -g localtunnel
fi

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "node.*simple-meet"
pkill -f "lt.*--port"
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

# Start localtunnel for backend
echo "🌐 Creating public URL for backend..."
lt --port 5001 --subdomain simple-meet-backend-$RANDOM > /tmp/lt-backend.log 2>&1 &
LT_BACKEND_PID=$!
sleep 3

# Get backend URL from log
BACKEND_URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" /tmp/lt-backend.log | head -1)

if [ -z "$BACKEND_URL" ]; then
    # Try without subdomain
    lt --port 5001 > /tmp/lt-backend2.log 2>&1 &
    LT_BACKEND_PID=$!
    sleep 3
    BACKEND_URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" /tmp/lt-backend2.log | head -1)
fi

echo "✅ Backend URL: $BACKEND_URL"

# Create .env.local file for frontend
echo "VITE_SOCKET_SERVER=$BACKEND_URL" > frontend/.env.local

# Update frontend to use environment variable
cat > frontend/src/config.js << EOF
export const SOCKET_SERVER = import.meta.env.VITE_SOCKET_SERVER || 'http://localhost:5001';
EOF

# Update MeetingPage to use config
sed -i.bak "s|const SOCKET_SERVER = .*|import { SOCKET_SERVER } from '../config';|" frontend/src/pages/MeetingPage.jsx

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3

# Start localtunnel for frontend
echo "🌐 Creating public URL for frontend..."
lt --port 3000 --subdomain simple-meet-$RANDOM > /tmp/lt-frontend.log 2>&1 &
LT_FRONTEND_PID=$!
sleep 3

# Get frontend URL
FRONTEND_URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" /tmp/lt-frontend.log | head -1)

if [ -z "$FRONTEND_URL" ]; then
    lt --port 3000 > /tmp/lt-frontend2.log 2>&1 &
    LT_FRONTEND_PID=$!
    sleep 3
    FRONTEND_URL=$(grep -o "https://[a-zA-Z0-9-]*\.loca\.lt" /tmp/lt-frontend2.log | head -1)
fi

echo ""
echo "🎉 Simple Meet is now publicly accessible!"
echo "================================================"
echo "📱 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo "================================================"
echo ""
echo "⚠️  Note: When accessing via localtunnel, you may need to:"
echo "1. Click 'Continue' on the localtunnel warning page"
echo "2. The page will show a password prompt - just click 'Submit'"
echo ""
echo "Local access:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID $LT_BACKEND_PID $LT_FRONTEND_PID 2>/dev/null
    rm -f frontend/.env.local frontend/src/config.js
    mv frontend/src/pages/MeetingPage.jsx.bak frontend/src/pages/MeetingPage.jsx 2>/dev/null
    exit
}

trap cleanup INT

# Wait
wait 