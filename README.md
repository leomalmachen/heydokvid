# Video Meeting Platform

A modern video conferencing platform built with FastAPI, LiveKit, and React.

## 🚀 Features

- Real-time video conferencing with LiveKit
- Room management and participant controls
- Recording capabilities
- Modern React frontend
- FastAPI backend with async support
- Redis for caching and session management
- PostgreSQL for data persistence

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- LiveKit Server (or cloud account)
- PostgreSQL
- Redis

## 🛠️ Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   ./start-local-development.sh
   ```

   Or manually:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

### Manual Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🏗️ Architecture

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core functionality (LiveKit, Redis, etc.)
│   │   ├── models/      # Database models
│   │   └── schemas/     # Pydantic schemas
│   └── requirements.txt
├── frontend/            # React frontend
├── infrastructure/      # Deployment configs
└── scripts/            # Utility scripts
```

## 🚀 Deployment

### Render.com
```bash
./deploy-render.sh
```

### Docker
```bash
docker build -t video-meeting-app .
docker run -p 8000:8000 video-meeting-app
```

### Environment Variables

Key environment variables:
- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key

See `env.example` for complete list.

## 📚 API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Run tests
pytest

# Test meeting system
python test_meeting_system.py
```

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 