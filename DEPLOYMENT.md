# Deployment Guide - HeyDok Video

## 🚀 GitHub Deployment Setup

### 1. Repository Setup
```bash
# Initialize git repository if not already done
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/heydok-video.git
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets
Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add these secrets:
- `HEROKU_API_KEY`: Your Heroku API key (found in Account Settings → API Key)
- `HEROKU_APP_NAME`: Your Heroku app name
- `HEROKU_EMAIL`: Your Heroku account email

## 🔧 Heroku Deployment

### Method 1: One-Click Deploy
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Method 2: Manual Heroku CLI
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create new Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set LIVEKIT_URL=wss://heydok-5pbd24sq.livekit.cloud
heroku config:set LIVEKIT_API_KEY=APIysK82G8HGmFr
heroku config:set LIVEKIT_API_SECRET=ytVhapnJwHIzfQzzqZL3sPbSJfelfdBcCtD2vCwm0bbA

# Deploy
git push heroku main

# Open your app
heroku open
```

### Method 3: GitHub Integration
1. Go to your Heroku Dashboard
2. Create new app
3. Go to Deploy tab
4. Connect to GitHub
5. Enable automatic deploys from main branch
6. Set Config Vars in Settings tab:
   - `LIVEKIT_URL`: `wss://heydok-5pbd24sq.livekit.cloud`
   - `LIVEKIT_API_KEY`: `APIysK82G8HGmFr`
   - `LIVEKIT_API_SECRET`: `ytVhapnJwHIzfQzzqZL3sPbSJfelfdBcCtD2vCwm0bbA`

## 🔍 Health Check URLs
After deployment, test these endpoints:
- `/health` - Application health status
- `/api/health` - API health status
- `/` - Homepage

## 🐛 Troubleshooting

### Common Issues:
1. **LiveKit credentials error**: Verify all three environment variables are set correctly
2. **Static files not found**: Make sure `frontend/` directory exists and contains HTML files
3. **Port binding error**: Heroku automatically sets the PORT variable

### Debug Commands:
```bash
# Check Heroku logs
heroku logs --tail

# Check config vars
heroku config

# Restart app
heroku restart
```

## 📝 Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `LIVEKIT_URL` | LiveKit WebSocket URL | Yes |
| `LIVEKIT_API_KEY` | LiveKit API Key | Yes |
| `LIVEKIT_API_SECRET` | LiveKit API Secret | Yes |
| `APP_URL` | Full app URL (auto-set by Heroku) | No |
| `PORT` | Port number (auto-set by Heroku) | No | 