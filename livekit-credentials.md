# LiveKit Configuration

## WebSocket URL
```
wss://malmachen-8s6xtzpq.livekit.cloud
```

## API Credentials
- **API Key**: `APIM4pxPvXu6uF4`
- **API Secret**: `FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A`

## Configuration Examples

### Environment Variables (.env)
```bash
LIVEKIT_API_KEY=APIM4pxPvXu6uF4
LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud
```

### Docker Compose
```yaml
environment:
  - LIVEKIT_API_KEY=APIM4pxPvXu6uF4
  - LIVEKIT_API_SECRET=FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
  - LIVEKIT_URL=wss://malmachen-8s6xtzpq.livekit.cloud
```

### Deployment (Render, Heroku, etc.)
Set these environment variables in your deployment platform:
- `LIVEKIT_API_KEY`: APIM4pxPvXu6uF4
- `LIVEKIT_API_SECRET`: FWueZ5yBMWcnYmC9uOyzBjeKIFz9kmN7mmogeaPcWr1A
- `LIVEKIT_URL`: wss://malmachen-8s6xtzpq.livekit.cloud

## Testing the Connection

You can test the LiveKit connection with this curl command:
```bash
curl -X POST http://localhost:8000/api/v1/meetings/create
```

This should create a meeting room on the LiveKit server and return:
```json
{
  "meeting_id": "abc-defg-hij",
  "meeting_link": "http://localhost:3000/meeting/abc-defg-hij",
  "created_at": "2024-01-15T10:30:00Z",
  "livekit_url": "wss://malmachen-8s6xtzpq.livekit.cloud"
}
```

## Important Notes

1. **Security**: Never commit these credentials to public repositories
2. **CORS**: Make sure to add your frontend URL to CORS_ORIGINS
3. **WebSocket**: The URL uses `wss://` for secure WebSocket connections
4. **Cloud Service**: This is a LiveKit Cloud instance (malmachen-8s6xtzpq) 