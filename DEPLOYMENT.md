# Deployment Guide

This guide covers deployment options for the Video Meeting Platform.

## 🚀 Deployment Options

### 1. Render.com (Recommended)

Render provides easy deployment with automatic SSL and scaling.

#### Prerequisites
- Render account
- GitHub repository
- Environment variables ready

#### Steps

1. **Prepare your repository**
   ```bash
   ./deploy-render.sh
   ```

2. **Create services on Render**
   - Go to [render.com](https://render.com)
   - Create a new Web Service
   - Connect your GitHub repository
   - Use the following settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Configure environment variables**
   Add these in Render dashboard:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   DATABASE_URL=your_postgres_url
   REDIS_URL=your_redis_url
   SECRET_KEY=your_secret_key
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be available at `https://your-app.onrender.com`

### 2. Docker Deployment

Docker provides consistent deployment across any platform.

#### Local Docker

1. **Build the image**
   ```bash
   docker build -t video-meeting-app .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 \
     -e LIVEKIT_URL=your_livekit_url \
     -e LIVEKIT_API_KEY=your_api_key \
     -e LIVEKIT_API_SECRET=your_api_secret \
     -e DATABASE_URL=your_postgres_url \
     -e REDIS_URL=your_redis_url \
     -e SECRET_KEY=your_secret_key \
     video-meeting-app
   ```

#### Docker Compose

1. **Start all services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Check logs**
   ```bash
   docker-compose logs -f
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

## 📋 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LIVEKIT_URL` | LiveKit server URL | `wss://your-livekit.com` |
| `LIVEKIT_API_KEY` | LiveKit API key | `APIxxxxxxxx` |
| `LIVEKIT_API_SECRET` | LiveKit API secret | `secret-key-here` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `SECRET_KEY` | App secret key | `your-secret-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed origins | `["*"]` |

## 🔍 Health Checks

### API Health
```bash
curl https://your-app.com/health
```

### LiveKit Connection
```bash
curl https://your-app.com/api/v1/health/livekit
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**
   - Change the PORT environment variable
   - Check for other services on the same port

2. **LiveKit connection errors**
   - Verify credentials are correct
   - Check LiveKit server is accessible
   - Ensure WebSocket connections are allowed

3. **Database connection issues**
   - Verify DATABASE_URL format
   - Check network connectivity
   - Ensure database is running

### Logs

- **Render**: Check logs in Render dashboard
- **Docker**: `docker logs container-name`
- **Local**: Check `logs/` directory

## 🔒 Security Considerations

1. **Use HTTPS in production**
2. **Set strong SECRET_KEY**
3. **Restrict CORS origins**
4. **Use environment variables for secrets**
5. **Enable rate limiting**
6. **Regular security updates**

## 📊 Monitoring

### Recommended Tools
- **Sentry** for error tracking
- **Prometheus** for metrics
- **Grafana** for visualization
- **Uptime monitoring** services

### Key Metrics
- Response times
- Error rates
- Active connections
- Room usage
- API usage

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations
```bash
alembic upgrade head
```

### Rolling Updates
1. Deploy new version
2. Run health checks
3. Switch traffic
4. Monitor for issues

## 📞 Support

For deployment issues:
1. Check logs first
2. Review environment variables
3. Test locally with same config
4. Check GitHub issues
5. Contact support if needed 