#!/bin/bash

# HeyDok Video - Local Development Server
echo "🚀 Starting HeyDok Video Server..."

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found! Please copy env.example to .env and configure your settings."
    echo "   cp env.example .env"
    exit 1
fi

# Verify required environment variables
if [ -z "$LIVEKIT_URL" ] || [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ]; then
    echo "❌ Missing required LiveKit environment variables!"
    echo "   Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in your .env file"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "🔗 LiveKit URL: $LIVEKIT_URL"
echo "🔑 API Key: ${LIVEKIT_API_KEY:0:10}..."

# Start the server
echo "🌟 Starting FastAPI server on http://localhost:8000"
python3 main.py 