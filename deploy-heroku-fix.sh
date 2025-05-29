#!/bin/bash

echo "🚀 Fixing Heroku Deployment for Video Meeting App"

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   brew tap heroku/brew && brew install heroku"
    exit 1
fi

# Login check
echo "📋 Checking Heroku login status..."
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please login to Heroku first:"
    heroku login
fi

# Get app name
read -p "Enter your Heroku app name (video-meeting-app-bdd88513864d): " APP_NAME
APP_NAME=${APP_NAME:-video-meeting-app-bdd88513864d}

echo "🔧 Setting up environment variables..."

# Set essential environment variables
heroku config:set LIVEKIT_URL="wss://google-meet-replacer-fcw5apmd.livekit.cloud" --app $APP_NAME
heroku config:set LIVEKIT_API_KEY="APIwkvkVSaRyTE3" --app $APP_NAME
heroku config:set LIVEKIT_API_SECRET="7FVh4h09qkZyejvgtV4Mc5Yo6uNgaMNVofxvCQBnRgf" --app $APP_NAME
heroku config:set ENVIRONMENT="production" --app $APP_NAME

echo "📦 Deploying updated code..."

# Add and commit changes
git add .
git commit -m "Fix Heroku deployment: simplified dependencies and fixed Procfile"

# Deploy to Heroku
git push heroku main

echo "🔍 Checking deployment status..."
heroku ps --app $APP_NAME

echo "📊 Showing recent logs..."
heroku logs --tail --app $APP_NAME &

echo ""
echo "✅ Deployment script completed!"
echo ""
echo "🌐 Your app should be available at: https://$APP_NAME.herokuapp.com"
echo ""
echo "🔧 If you still see issues, run:"
echo "   heroku restart --app $APP_NAME"
echo "   heroku logs --tail --app $APP_NAME"
echo ""
echo "💡 The main fixes applied:"
echo "   - Simplified requirements.txt to reduce boot time"
echo "   - Fixed Procfile with single worker"
echo "   - Set correct LiveKit environment variables"
echo "   - Added production environment flag" 