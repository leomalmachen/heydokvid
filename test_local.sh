#!/bin/bash
# Test script for local development

echo "Starting HeyDok Video locally..."
echo "================================"

# Export LiveKit credentials
export LIVEKIT_URL="wss://heydok-5pbd24sq.livekit.cloud"
export LIVEKIT_API_KEY="APIyJXxGmFr"
export LIVEKIT_API_SECRET="ytVhgzwOaAz6IwT4yA7TFiKrLGFE50bbA"
export APP_URL="http://localhost:8000"

# Start the server
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
python3 main.py 