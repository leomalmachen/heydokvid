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

## 🚀 Heroku Deployment Guide

### Prerequisites
- Heroku CLI installed
- Git repository with your code
- LiveKit Cloud account

### 1. Create Heroku App
```bash
heroku create your-app-name
```

### 2. Set Environment Variables
```bash
# Required LiveKit Configuration (get these from your LiveKit Cloud dashboard)
heroku config:set LIVEKIT_URL=wss://your-project-id.livekit.cloud
heroku config:set LIVEKIT_API_KEY=your_api_key_here
heroku config:set LIVEKIT_API_SECRET=your_api_secret_here

# App Configuration
heroku config:set SECRET_KEY=your-super-secret-key-min-32-chars
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false
heroku config:set ALLOWED_ORIGINS=https://your-app-name.herokuapp.com

# Database (Heroku Postgres addon will set DATABASE_URL automatically)
heroku addons:create heroku-postgresql:essential-0
```

### 3. Deploy
```bash
git push heroku main
```

### 4. Verify Deployment
```bash
heroku logs --tail
heroku open
```

## Environment Variables Reference

### Required
- `LIVEKIT_URL`: `wss://your-project-id.livekit.cloud`
- `LIVEKIT_API_KEY`: `your_api_key_here`
- `LIVEKIT_API_SECRET`: `your_api_secret_here`

### Optional
- `SECRET_KEY`: Random 32+ character string
- `ENVIRONMENT`: `production`
- `DEBUG`: `false`
- `ALLOWED_ORIGINS`: Your domain(s)

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