# Deployment Configuration

## Environment Variables

Set these environment variables in your deployment platform:

### Required Variables

```bash
# LiveKit Configuration
LIVEKIT_API_KEY=APIM4pxPvXu6uF4
LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud

# Application Settings
SECRET_KEY=your-production-secret-key-change-this
ENVIRONMENT=production
DEBUG=False

# Frontend URL (adjust based on your deployment)
FRONTEND_URL=https://video-meeting-app-two.vercel.app
```

### Optional Variables

```bash
# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (if using Redis)
REDIS_URL=redis://host:6379/0

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

## Platform-Specific Instructions

### Render.com

1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Add each variable above

### Heroku

```bash
heroku config:set LIVEKIT_API_KEY=APIM4pxPvXu6uF4
heroku config:set LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
heroku config:set LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=False
heroku config:set FRONTEND_URL=https://video-meeting-app-two.vercel.app
```

### Railway

Add to `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Then set environment variables in Railway dashboard.

### Vercel (for Frontend)

In your Vercel project settings, add:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud
```

## Testing the Deployment

After deployment, test the API:

```bash
# Create a meeting
curl -X POST https://your-app-url.com/api/v1/meetings/create

# Check health
curl https://your-app-url.com/health
```

## Security Notes

1. **Change SECRET_KEY**: Always use a strong, unique secret key in production
2. **HTTPS Only**: Ensure your deployment uses HTTPS
3. **CORS**: Update CORS_ORIGINS in config.py to include your production URLs
4. **Environment**: Never commit credentials to version control 