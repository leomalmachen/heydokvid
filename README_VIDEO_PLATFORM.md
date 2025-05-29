# Video Meeting Platform (Google Meet Style)

Eine einfache, moderne Videoplattform im Stil von Google Meet, gebaut mit React, FastAPI und LiveKit.

## Features

- **Ein-Klick Meeting-Erstellung** - Keine Registrierung erforderlich
- **Öffentliche Meeting-Links** - Teilen Sie einfach den Link
- **HD Video & Audio** - Powered by LiveKit
- **Screen Sharing** - Bildschirmfreigabe unterstützt
- **Responsive Design** - Funktioniert auf Desktop und Mobile
- **Automatisches Cleanup** - Meetings laufen 24 Stunden

## Architektur

### Backend (FastAPI)
- `backend/main.py` - Haupt-API mit Meeting-Management
- Endpoints:
  - `POST /api/v1/meetings/create` - Erstellt neues Meeting
  - `POST /api/v1/meetings/{id}/join` - Tritt Meeting bei
  - `GET /api/v1/meetings/{id}/info` - Meeting-Informationen
  - `DELETE /api/v1/meetings/{id}/leave/{participant_id}` - Verlässt Meeting

### Frontend (React + TypeScript)
- `HomePage.tsx` - Startseite mit Meeting-Erstellung
- `MeetingLobby.tsx` - Namenseingabe vor dem Beitritt
- `MeetingRoom.tsx` - Video-Konferenz-Raum mit LiveKit

## Installation & Start

### Voraussetzungen
- Node.js 16+
- Python 3.8+
- LiveKit Server läuft auf `localhost:7880`

### Backend starten

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Das Backend läuft auf `http://localhost:8000`

### Frontend starten

```bash
cd frontend/heydok-video-frontend
npm install
npm start
```

Das Frontend läuft auf `http://localhost:3000`

### LiveKit Server starten

```bash
docker run --rm \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: secret" \
  livekit/livekit-server \
  --dev \
  --node-ip=127.0.0.1
```

## Verwendung

1. Öffnen Sie `http://localhost:3000`
2. Klicken Sie auf "Neues Meeting"
3. Teilen Sie den generierten Link
4. Teilnehmer geben ihren Namen ein und treten bei

## Meeting-Link Format

- Format: `http://localhost:3000/meeting/xxx-xxxx-xxx`
- Beispiel: `http://localhost:3000/meeting/abc-defg-hij`
- Links sind 24 Stunden gültig

## Entwicklung

### Umgebungsvariablen

Erstellen Sie eine `.env` Datei im Frontend:

```env
REACT_APP_API_URL=http://localhost:8000
```

### TypeScript Types

Die API-Typen sind in `src/services/api.ts` definiert.

### Styling

- Tailwind CSS für Utility-First Styling
- LiveKit Components mit Custom Theme
- Responsive Grid Layout

## Sicherheit

- Meetings laufen automatisch nach 24 Stunden ab
- Keine Benutzerdaten werden gespeichert
- JWT-Token für sichere LiveKit-Verbindungen
- CORS konfiguriert für lokale Entwicklung

## Troubleshooting

### "Meeting nicht gefunden"
- Meeting ist abgelaufen (>24 Stunden)
- Falscher Meeting-Code
- Backend nicht erreichbar

### Video/Audio funktioniert nicht
- LiveKit Server läuft nicht
- Browser-Berechtigungen verweigert
- Firewall blockiert WebRTC

### CORS-Fehler
- Backend CORS-Konfiguration prüfen
- Frontend läuft auf richtigem Port

## Nächste Schritte

- [ ] Persistente Datenspeicherung (Redis/PostgreSQL)
- [ ] Meeting-Passwortschutz
- [ ] Chat-Funktion
- [ ] Aufzeichnung
- [ ] Virtuelle Hintergründe
- [ ] Meeting-Zeitplanung 