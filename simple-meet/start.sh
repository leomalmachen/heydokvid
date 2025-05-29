#!/bin/bash

echo "🚀 Starting Simple Meet..."

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
npm install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install

# Start both servers
echo "🎬 Starting servers..."
cd ../backend
npm start &
BACKEND_PID=$!

cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Simple Meet is running!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend: http://localhost:5001"
echo ""
echo "🔗 Create a meeting and share the link with others!"
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 