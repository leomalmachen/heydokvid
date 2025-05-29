# Deployment Guide - Video Meeting App

This guide explains how to deploy your video meeting application to Render.com.

## 🏗️ Architecture Overview

The application consists of two main services:

1. **Simple Video Meeting App** (`video-meeting-app`)
   - Runtime: Python 3.11
   - Entry point: `backend/main.py`
   - Standalone FastAPI application
   - No database dependencies

2. **Full Backend API** (`heydok-video-backend`)
   - Runtime: Docker
   - Entry point: `backend/app/main.py`
   - Full-featured application with database and Redis
   - HIPAA/GDPR compliant features

## 🚀 Quick Deployment

### Prerequisites

1. GitHub account with your code repository
2. Render.com account
3. LiveKit account and credentials

### Step 1: Prepare Your Repository

1. Ensure all changes are committed and pushed to GitHub
2. Run the deployment preparation script:
   ```bash
   ./deploy-render.sh
   ```

### Step 2: Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the services and click "Apply"

## 📋 Services Configuration

### Simple App (video-meeting-app)

- **URL**: `https://video-meeting-app.onrender.com`
- **Health Check**: `/health`
- **Auto Deploy**: Enabled
- **Environment Variables**:
  - `LIVEKIT_API_KEY`: Your LiveKit API key
  - `LIVEKIT_API_SECRET`: Your LiveKit API secret
  - `LIVEKIT_URL`: Your LiveKit WebSocket URL
  - `ENVIRONMENT`: production
  - `PORT`: 10000

### Full Backend (heydok-video-backend)

- **URL**: `https://heydok-video-backend.onrender.com`
- **Health Check**: `/health`
- **Auto Deploy**: Disabled (manual deployment)
- **Dependencies**: PostgreSQL database, Redis cache
- **Environment Variables**:
  - Database and Redis URLs (auto-configured)
  - LiveKit credentials
  - Security keys (auto-generated)
  - CORS and host settings

### Database (heydok-video-db)

- **Type**: PostgreSQL
- **Plan**: Starter
- **Database Name**: heydok_video
- **User**: heydok

### Cache (heydok-video-redis)

- **Type**: Redis
- **Plan**: Starter
- **IP Allow List**: Empty (accessible by services)

## 🔧 Configuration Files

### Requirements Files

- `backend/requirements.txt`: Full development dependencies
- `backend/requirements-production.txt`: Production-only dependencies (optimized)

### Docker Configuration

- `backend/Dockerfile`: Optimized for production deployment
- Uses Python 3.11 slim image
- Non-root user for security
- Health checks included

### Render Configuration

- `render.yaml`: Complete service definitions
- Environment variables
- Service dependencies
- Health check endpoints

## 🔍 Monitoring and Debugging

### Health Checks

Both services expose health check endpoints:

```bash
# Simple app
curl https://video-meeting-app.onrender.com/health

# Full backend
curl https://heydok-video-backend.onrender.com/health
```

### Logs

View logs in the Render dashboard:
1. Go to your service
2. Click on "Logs" tab
3. Monitor real-time logs

### API Documentation

For the full backend (when DEBUG=true):
- API Docs: `https://heydok-video-backend.onrender.com/api/docs`
- ReDoc: `https://heydok-video-backend.onrender.com/api/redoc`

## 🔐 Security Considerations

### Environment Variables

The following are auto-generated for security:
- `SECRET_KEY`: Application secret key
- `JWT_SECRET`: JWT signing secret
- `ENCRYPTION_KEY`: Data encryption key

### CORS Configuration

Update CORS origins in `render.yaml` to match your frontend domains:
```yaml
- key: CORS_ORIGINS
  value: https://your-frontend.netlify.app,https://your-backend.onrender.com
```

### Allowed Hosts

Configure allowed hosts for the full backend:
```yaml
- key: ALLOWED_HOSTS
  value: your-backend.onrender.com,localhost
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all dependencies in `requirements-production.txt` are valid
   - Ensure Python version compatibility (3.11)

2. **Service Won't Start**
   - Check environment variables are set correctly
   - Verify health check endpoint is accessible
   - Review logs for error messages

3. **Database Connection Issues**
   - Ensure database service is running
   - Check `DATABASE_URL` environment variable
   - Verify database credentials

4. **LiveKit Connection Issues**
   - Verify LiveKit credentials are correct
   - Check LiveKit URL format (should start with `wss://`)
   - Ensure LiveKit service is active

### Debug Commands

```bash
# Check service status
curl -I https://your-app.onrender.com/health

# Test database connection (from app logs)
# Look for database connection messages in logs

# Test Redis connection (from app logs)
# Look for Redis connection messages in logs
```

## 📈 Scaling and Performance

### Resource Limits

Render Starter plans include:
- 512 MB RAM
- 0.1 CPU
- 10 GB bandwidth/month

### Optimization Tips

1. **Use Production Requirements**
   - Excludes development and testing dependencies
   - Faster build times
   - Smaller container size

2. **Enable Caching**
   - Docker layer caching
   - Pip cache for dependencies

3. **Monitor Performance**
   - Use health check endpoints
   - Monitor response times
   - Check resource usage in dashboard

## 🔄 Updates and Maintenance

### Updating Dependencies

1. Update `requirements-production.txt`
2. Test locally
3. Commit and push changes
4. Redeploy services

### Database Migrations

For the full backend with database:
1. Create migration files
2. Deploy backend service
3. Migrations run automatically on startup

### Rolling Back

1. Go to Render dashboard
2. Select service
3. Go to "Deploys" tab
4. Click "Redeploy" on previous successful deployment

## 📞 Support

### Render Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

### Application Support

- Check application logs in Render dashboard
- Review health check endpoints
- Monitor service dependencies

---

## 🎯 Next Steps

After successful deployment:

1. **Test the Application**
   - Visit the deployed URLs
   - Test video meeting functionality
   - Verify LiveKit integration

2. **Configure Frontend**
   - Update frontend to use production API URLs
   - Deploy frontend to Netlify or similar

3. **Set Up Monitoring**
   - Configure alerts for service downtime
   - Set up log aggregation if needed
   - Monitor performance metrics

4. **Security Review**
   - Review environment variables
   - Check CORS settings
   - Verify SSL certificates

Happy deploying! 🚀 