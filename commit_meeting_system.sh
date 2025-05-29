#!/bin/bash

# Video Meeting System - Git Commit Script
# Commits all improvements to the meeting system

echo "🎥 Video Meeting System - Git Commit"
echo "===================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Add all changes
echo "📁 Adding all changes..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
    exit 0
fi

# Show what will be committed
echo "📋 Changes to be committed:"
git diff --cached --name-status

echo ""
read -p "🤔 Do you want to commit these changes? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Commit cancelled"
    exit 1
fi

# Create commit message
COMMIT_MESSAGE="🎥 Implement complete video meeting system with LiveKit

✨ Features implemented:
- Complete LiveKit integration with persistent room creation
- Google Meet style meeting IDs (xxx-xxxx-xxx format)
- Shareable meeting links (/meeting/:roomId)
- Robust token generation for participants
- Comprehensive error handling and logging
- Structured API architecture with proper separation
- Automated test suite for system validation
- Database persistence for meeting data

🔧 Technical improvements:
- Removed duplicate API implementations
- Cleaned up codebase structure
- Enhanced LiveKit client with proper room management
- Added comprehensive logging throughout
- Implemented proper URL routing for meetings
- Added health checks and monitoring endpoints

🧪 Testing & Documentation:
- Complete test suite (test_meeting_system.py)
- Startup script with environment validation
- Comprehensive README with setup instructions
- API documentation with examples

🚀 Ready for deployment:
- Docker support
- Environment configuration
- Production-ready error handling
- Security considerations implemented

This implementation provides a fully functional video meeting system
that can create rooms, generate shareable links, and allow multiple
participants to join the same LiveKit room using the same meeting ID."

# Commit the changes
echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

if [ $? -eq 0 ]; then
    echo "✅ Changes committed successfully!"
    
    # Ask about pushing
    echo ""
    read -p "🚀 Do you want to push to remote repository? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if remote exists
        if git remote | grep -q "origin"; then
            echo "📤 Pushing to origin..."
            git push origin $(git branch --show-current)
            
            if [ $? -eq 0 ]; then
                echo "✅ Successfully pushed to remote repository!"
            else
                echo "❌ Failed to push to remote repository"
                exit 1
            fi
        else
            echo "⚠️  No remote repository configured"
            echo "💡 Add a remote with: git remote add origin <repository-url>"
        fi
    else
        echo "ℹ️  Changes committed locally only"
    fi
    
    echo ""
    echo "🎉 Video Meeting System implementation complete!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Set up environment variables (.env file)"
    echo "   2. Start the system: python backend/start_meeting_system.py"
    echo "   3. Run tests: python backend/test_meeting_system.py"
    echo "   4. Access API docs: http://localhost:8000/api/docs"
    echo ""
    echo "📖 See backend/README_MEETING_SYSTEM.md for detailed documentation"
    
else
    echo "❌ Failed to commit changes"
    exit 1
fi 