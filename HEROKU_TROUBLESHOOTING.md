# 🚨 Heroku Deployment Troubleshooting Guide

## Problem: App Boot Timeout (Error R10, H20)

Your Heroku logs show:
- `Error R10 (Boot timeout) -> Web process failed to bind to $PORT within 60 seconds`
- `Error H20 desc="App boot timeout"`
- `Error H10 desc="App crashed"`

## 🔧 Quick Fix

Run the automated fix script:
```bash
./deploy-heroku-fix.sh
```

## 🛠 Manual Fix Steps

### 1. Simplify Dependencies
The main issue is likely too many heavy dependencies causing slow boot time.

**Fixed:** Simplified `requirements.txt` to only essential packages:
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- python-multipart==0.0.6
- pyjwt==2.8.0
- pydantic==2.4.2
- python-dotenv==1.0.0

### 2. Fix Procfile
**Fixed:** Updated `Procfile` to use single worker:
```
web: cd backend && python -m uvicorn simple_meetings_api:app --host 0.0.0.0 --port $PORT --workers 1
```

### 3. Set Environment Variables
```bash
heroku config:set LIVEKIT_URL="wss://google-meet-replacer-fcw5apmd.livekit.cloud" --app your-app-name
heroku config:set LIVEKIT_API_KEY="APIwkvkVSaRyTE3" --app your-app-name
heroku config:set LIVEKIT_API_SECRET="7FVh4h09qkZyejvgtV4Mc5Yo6uNgaMNVofxvCQBnRgf" --app your-app-name
heroku config:set ENVIRONMENT="production" --app your-app-name
```

### 4. Deploy Fixed Version
```bash
git add .
git commit -m "Fix Heroku deployment issues"
git push heroku main
```

### 5. Restart App
```bash
heroku restart --app your-app-name
```

## 🔍 Verification Steps

### Check App Status
```bash
heroku ps --app your-app-name
```

### Monitor Logs
```bash
heroku logs --tail --app your-app-name
```

### Test Health Endpoint
```bash
curl https://your-app-name.herokuapp.com/health
```

## 🎯 Expected Results

After the fix, you should see:
- ✅ App starts within 30 seconds
- ✅ No more R10/H20 errors
- ✅ Health endpoint returns `{"status": "healthy"}`
- ✅ Main page loads at your Heroku URL

## 🚨 If Issues Persist

### Check Build Logs
```bash
heroku logs --app your-app-name | grep "Build"
```

### Verify Environment Variables
```bash
heroku config --app your-app-name
```

### Scale Down and Up
```bash
heroku ps:scale web=0 --app your-app-name
heroku ps:scale web=1 --app your-app-name
```

### Check Dyno Type
```bash
heroku ps:type --app your-app-name
```

## 💡 Root Cause Analysis

The original issues were:
1. **Heavy Dependencies**: Too many packages in requirements.txt
2. **Multiple Workers**: Uvicorn trying to start multiple workers
3. **Missing Environment Variables**: LiveKit configuration not set
4. **Slow Startup**: App taking >60 seconds to bind to port

## 🔗 Useful Commands

```bash
# Check app info
heroku info --app your-app-name

# View config vars
heroku config --app your-app-name

# Open app in browser
heroku open --app your-app-name

# View recent releases
heroku releases --app your-app-name

# Rollback if needed
heroku rollback --app your-app-name
```

## 📞 Support

If you continue to have issues:
1. Check the logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure your LiveKit credentials are valid
4. Test the app locally first with `./start-video-meetings.sh` 