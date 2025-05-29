#!/bin/bash

echo "🚀 Deploying Video Meeting App..."

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Installing..."
    curl -fsSL https://cli.render.com/install | sh
fi

# Deploy to Render
echo "📦 Deploying to Render..."
render deploy

echo "✅ Deployment initiated!"
echo "🌐 Your app will be available at: https://video-meeting-app.onrender.com"
echo "📋 Check deployment status at: https://dashboard.render.com" 