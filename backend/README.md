# Backend - Simple Video Meetings API

This is the backend API for the Simple Video Meetings platform, built with FastAPI.

## Structure

```
backend/
├── simple_meetings_api.py    # Main API server
├── main.py                   # Alternative API implementation (not used)
├── app/                      # Application modules (for future expansion)
├── requirements.txt          # Python dependencies
├── requirements-minimal.txt  # Minimal dependencies
├── Dockerfile               # Docker configuration
└── scripts/                 # Utility scripts
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-minimal.txt
```

## Running the Server

```bash
python -m uvicorn simple_meetings_api:app --reload --port 8001
```

The API will be available at http://localhost:8001

## API Endpoints

- `POST /api/v1/meetings/create` - Create a new meeting
- `POST /api/v1/meetings/{meeting_id}/join` - Join a meeting
- `GET /api/v1/meetings/{meeting_id}/info` - Get meeting information
- `DELETE /api/v1/meetings/{meeting_id}` - End a meeting
- `GET /health` - Health check

## Environment Variables

- `LIVEKIT_URL` - LiveKit server URL (default: ws://localhost:7880)
- `LIVEKIT_API_KEY` - LiveKit API key (default: devkey)
- `LIVEKIT_API_SECRET` - LiveKit API secret (default: secret)
- `FRONTEND_URL` - Frontend URL for meeting links (default: http://localhost:3001)

## Development

The server uses in-memory storage for meetings during development. In production, this should be replaced with a proper database.

Meetings expire after 24 hours and are automatically cleaned up. 