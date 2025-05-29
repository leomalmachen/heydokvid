# Simple Video Meetings Platform

Eine einfache Videokonferenzplattform im Stil von Google Meet, die es Benutzern ermöglicht, mit einem Klick Meetings zu erstellen und ohne Registrierung beizutreten.

## Features

- **Ein-Klick Meeting-Erstellung**: Erstellen Sie sofort ein neues Meeting
- **Öffentliche Links**: Teilen Sie den Meeting-Link mit jedem
- **Keine Registrierung erforderlich**: Geben Sie einfach Ihren Namen ein und treten Sie bei
- **Video & Audio**: Vollständige Videokonferenz-Funktionalität
- **Modernes UI**: Sauberes, Google Meet-ähnliches Design

## Technologie-Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React mit TypeScript
- **Video**: WebRTC (mit LiveKit-Integration vorbereitet)
- **Styling**: CSS mit modernem Dark Theme

## Installation & Start

### Backend starten

1. Navigieren Sie zum Backend-Verzeichnis:
```bash
cd backend/backend
```

2. Installieren Sie die Abhängigkeiten (falls noch nicht geschehen):
```bash
pip install fastapi uvicorn python-dotenv livekit
```

3. Starten Sie den Server:
```bash
python -m uvicorn simple_meetings_api:app --reload --port 8001
```

Das Backend läuft nun auf http://localhost:8001

### Frontend starten

1. Navigieren Sie zum Frontend-Verzeichnis:
```bash
cd frontend/heydok-video-frontend
```

2. Installieren Sie die Abhängigkeiten:
```bash
npm install
```

3. Starten Sie die Entwicklungsumgebung:
```bash
PORT=3001 npm start
```

Das Frontend läuft nun auf http://localhost:3001

## Verwendung

1. Öffnen Sie http://localhost:3001 in Ihrem Browser
2. Klicken Sie auf "Neues Meeting" um ein Meeting zu erstellen
3. Teilen Sie den generierten Link mit anderen Teilnehmern
4. Teilnehmer können dem Meeting beitreten, indem sie:
   - Den Link direkt öffnen
   - Den Meeting-Code auf der Startseite eingeben
5. Geben Sie Ihren Namen ein und klicken Sie auf "Join now"

## API Endpoints

- `POST /api/v1/meetings/create` - Erstellt ein neues Meeting
- `POST /api/v1/meetings/{meeting_id}/join` - Tritt einem Meeting bei
- `GET /api/v1/meetings/{meeting_id}/info` - Ruft Meeting-Informationen ab
- `DELETE /api/v1/meetings/{meeting_id}` - Beendet ein Meeting
- `GET /health` - Health Check Endpoint

## Projektstruktur

```
backend/
├── backend/
│   ├── simple_meetings_api.py  # Haupt-API Server
│   └── ...
frontend/
├── heydok-video-frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.tsx      # Startseite
│   │   │   └── MeetingPage.tsx   # Meeting Lobby & Raum
│   │   ├── components/
│   │   │   └── VideoRoom.tsx     # Video-Konferenz Komponente
│   │   ├── styles/
│   │   │   ├── MeetingPage.css   # Meeting-Seite Styles
│   │   │   └── VideoRoom.css     # Video-Raum Styles
│   │   └── services/
│   │       └── api.ts            # API Service
│   └── ...
```

## Nächste Schritte

1. **LiveKit Integration**: Vollständige WebRTC-Funktionalität mit LiveKit
2. **Persistenz**: Datenbank-Integration statt In-Memory Storage
3. **Deployment**: Docker-Setup und Cloud-Deployment
4. **Features**: Chat, Bildschirmfreigabe, Aufzeichnung

## Hinweise

- Das System verwendet derzeit lokale Media-Streams für die Video-Vorschau
- Für echte Videokonferenzen muss LiveKit konfiguriert und gestartet werden
- Meeting-Links sind 24 Stunden gültig 