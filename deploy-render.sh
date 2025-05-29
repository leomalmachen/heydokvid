#!/bin/bash

# Render Deployment Script for Video Meeting App
# This script helps with deploying to Render.com

set -e

echo "🚀 Preparing deployment to Render..."

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run this script from the project root."
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend/backend" ]; then
    echo "❌ Error: backend/backend directory not found."
    exit 1
fi

# Validate requirements files
echo "📋 Validating requirements files..."

if [ ! -f "backend/backend/requirements.txt" ]; then
    echo "❌ Error: backend/backend/requirements.txt not found."
    exit 1
fi

if [ ! -f "backend/backend/requirements-production.txt" ]; then
    echo "❌ Error: backend/backend/requirements-production.txt not found."
    exit 1
fi

# Check for main application files
if [ ! -f "backend/backend/main.py" ]; then
    echo "❌ Error: backend/backend/main.py not found."
    exit 1
fi

if [ ! -f "backend/backend/app/main.py" ]; then
    echo "❌ Error: backend/backend/app/main.py not found."
    exit 1
fi

# Check Dockerfile
if [ ! -f "backend/backend/Dockerfile" ]; then
    echo "❌ Error: backend/backend/Dockerfile not found."
    exit 1
fi

echo "✅ All required files found."

# Display deployment information
echo ""
echo "📊 Deployment Configuration:"
echo "  - Simple App: video-meeting-app (Python runtime)"
echo "  - Full App: heydok-video-backend (Docker runtime)"
echo "  - Database: heydok-video-db (PostgreSQL)"
echo "  - Cache: heydok-video-redis (Redis)"
echo ""

# Check if git is clean
if command -v git &> /dev/null; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  Warning: You have uncommitted changes."
        echo "   It's recommended to commit all changes before deploying."
        echo ""
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled."
            exit 1
        fi
    else
        echo "✅ Git repository is clean."
    fi
fi

echo ""
echo "🔧 Deployment Steps:"
echo "1. Commit and push your changes to GitHub"
echo "2. Go to your Render dashboard"
echo "3. Connect your GitHub repository"
echo "4. Render will automatically detect the render.yaml file"
echo "5. Review the services and deploy"
echo ""

echo "📝 Important Notes:"
echo "- The simple app (video-meeting-app) will be available at: https://video-meeting-app.onrender.com"
echo "- The full app (heydok-video-backend) will be available at: https://heydok-video-backend.onrender.com"
echo "- Make sure your LiveKit credentials are correct"
echo "- Database and Redis will be automatically provisioned"
echo ""

echo "🔗 Useful Commands:"
echo "  - View logs: Check Render dashboard"
echo "  - Health check: curl https://your-app.onrender.com/health"
echo "  - API docs: https://your-app.onrender.com/api/docs (if DEBUG=true)"
echo ""

echo "✅ Deployment preparation complete!"
echo "   Push your changes to GitHub and deploy via Render dashboard." 