# Meeting API Documentation

## Overview

This API provides a complete video meeting system using LiveKit. It allows creating persistent meeting rooms, generating shareable links, and managing participants.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Create Meeting

Creates a new meeting room on the LiveKit server.

**Endpoint:** `POST /meetings/create`

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "meeting_link": "http://localhost:3000/meeting/abc-defg-hij",
  "created_at": "2024-01-15T10:30:00Z",
  "livekit_url": "ws://localhost:7880"
}
```

### 2. Join Meeting

Join an existing meeting room.

**Endpoint:** `POST /meetings/{meeting_id}/join`

**Request Body:**
```json
{
  "user_name": "John Doe"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "meeting_id": "abc-defg-hij",
  "user_name": "John Doe",
  "livekit_url": "ws://localhost:7880",
  "user_id": "john_doe_a1b2c3d4"
}
```

### 3. Get Meeting Info

Get information about a meeting.

**Endpoint:** `GET /meetings/{meeting_id}/info`

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "exists": true,
  "num_participants": 2,
  "created_at": "2024-01-15T10:30:00Z",
  "max_participants": 50
}
```

### 4. Check Meeting Exists

Quick check if a meeting exists.

**Endpoint:** `GET /meetings/{meeting_id}/exists`

**Response:**
```json
{
  "exists": true,
  "meeting_id": "abc-defg-hij"
}
```

### 5. List Participants

Get all participants in a meeting.

**Endpoint:** `GET /meetings/{meeting_id}/participants`

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "participants": [
    {
      "sid": "PA_xxx",
      "identity": "john_doe_a1b2c3d4",
      "name": "John Doe",
      "state": "ACTIVE",
      "joined_at": 1705315800
    }
  ],
  "count": 1
}
```

### 6. Delete Meeting

Delete a meeting room.

**Endpoint:** `DELETE /meetings/{meeting_id}`

**Response:**
```json
{
  "success": true,
  "message": "Meeting deleted successfully",
  "meeting_id": "abc-defg-hij"
}
```

## Meeting Flow

1. **Create Meeting**: User A creates a meeting and receives a meeting link
2. **Share Link**: User A shares the link (e.g., `http://localhost:3000/meeting/abc-defg-hij`)
3. **Join Meeting**: User B opens the link and joins with their name
4. **Connect**: Both users are connected to the same LiveKit room

## Error Responses

### 404 Not Found
```json
{
  "detail": "Meeting not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create meeting: [error details]"
}
```

## Testing

Use the provided `test_meeting_api.py` script to test all endpoints:

```bash
python test_meeting_api.py
```

## Environment Variables

- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `LIVEKIT_URL`: LiveKit server URL
- `FRONTEND_URL`: Frontend URL for generating meeting links 