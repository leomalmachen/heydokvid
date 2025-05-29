#!/bin/bash

echo "🚀 Starting Simple Meet..."
echo ""

# Kill existing processes
pkill -f "node.*simple-meet" 2>/dev/null
sleep 1

# Check dependencies
if [ ! -d "backend/node_modules" ]; then
    echo "📦 Installing backend dependencies..."
    cd backend && npm install && cd ..
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend
echo "🖥️  Starting backend server on port 5001..."
cd backend
PORT=5001 npm start &
BACKEND_PID=$!
cd ..
sleep 2

# Start frontend
echo "🎨 Starting frontend on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Simple Meet is running locally!"
echo "================================================"
echo "📍 Open in browser: http://localhost:3000"
echo "================================================"
echo ""
echo "🌐 To make it publicly accessible:"
echo ""
echo "Option 1 - Using ngrok (recommended):"
echo "  1. Install ngrok: brew install ngrok/ngrok/ngrok"
echo "  2. In new terminal: ngrok http 5001"
echo "  3. Copy the https URL (e.g., https://abc123.ngrok-free.app)"
echo "  4. Create frontend/.env.local with:"
echo "     VITE_SOCKET_SERVER=https://abc123.ngrok-free.app"
echo "  5. Restart this script"
echo "  6. In another terminal: ngrok http 3000"
echo "  7. Share the frontend ngrok URL"
echo ""
echo "Option 2 - Using localtunnel:"
echo "  1. npm install -g localtunnel"
echo "  2. In new terminal: lt --port 5001"
echo "  3. In another terminal: lt --port 3000"
echo "  Note: Visitors must click through the password page"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup INT

# Wait
wait 