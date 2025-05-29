# Frontend - Simple Video Meetings

React-based frontend for the Simple Video Meetings platform with TypeScript.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in this directory:
```
REACT_APP_API_URL=http://localhost:8001/api/v1
REACT_APP_LIVEKIT_URL=wss://your-livekit-server.com
```

3. Start the development server:
```bash
PORT=3001 npm start
```

The app will be available at http://localhost:3001

## TypeScript Configuration

The project uses Create React App with TypeScript. Some important configurations:

- `tsconfig.json` has been updated to include proper React types
- A custom type declaration file (`src/types/livekit.d.ts`) has been added to fix LiveKit component type issues with React 18
- Environment variables use `process.env.REACT_APP_*` pattern (not `import.meta.env`)

## Project Structure

```
src/
├── pages/
│   ├── HomePage.tsx        # Landing page
│   ├── MeetingRoom.tsx    # Video conference room
│   ├── SimpleMeeting.tsx  # Simple meeting join flow
│   └── VideoRoom.tsx      # Alternative video room implementation
├── services/
│   ├── api.ts            # Main API service
│   ├── meetingService.ts # Meeting-specific API calls
│   ├── auth.ts          # Authentication service
│   └── rooms.ts         # Room management service
├── components/          # Reusable components
├── contexts/           # React contexts
└── types/             # TypeScript type definitions
```

## Available Scripts

- `npm start` - Run development server
- `npm build` - Build for production
- `npm test` - Run tests

## Notes

- The app uses LiveKit for WebRTC video conferencing
- All API calls default to `http://localhost:8001/api/v1`
- Meeting links are in the format `/meeting/{meeting-id}`
- No authentication is required for joining meetings 