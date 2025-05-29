# Vereinfachtes Meeting-System (Google Meet Style)

## Übersicht

Das System wurde vereinfacht, um wie Google Meet zu funktionieren:
- **Ein Klick** erstellt ein Meeting
- **Ein Link** zum Teilen
- **Jeder mit dem Link** kann direkt beitreten
- **Keine Registrierung/Login** erforderlich

## API Endpoints

### 1. Meeting erstellen
```
POST /api/v1/meetings/create
```

**Request Body (optional):**
```json
{
  "name": "Team Meeting"  // Optional
}
```

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "meeting_url": "https://meet.heydok.com/meeting/abc-defg-hij",
  "created_at": "2024-01-01T10:00:00Z",
  "expires_at": "2024-01-02T10:00:00Z"
}
```

### 2. Meeting beitreten
```
POST /api/v1/meetings/{meeting_id}/join
```

**Request Body:**
```json
{
  "display_name": "John Doe"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "meeting_id": "abc-defg-hij",
  "livekit_url": "wss://livekit.heydok.com",
  "participant_id": "guest-a1b2c3d4"
}
```

### 3. Meeting-Info abrufen
```
GET /api/v1/meetings/{meeting_id}/info
```

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "meeting_url": "https://meet.heydok.com/meeting/abc-defg-hij",
  "created_at": "2024-01-01T10:00:00Z",
  "expires_at": "2024-01-02T10:00:00Z",
  "status": "active"
}
```

## Frontend-Nutzung

### Homepage (/)
- Ein großer Button "Start a new meeting"
- Eingabefeld für Meeting-Link/Code
- Keine Anmeldung erforderlich

### Meeting-Seite (/meeting/{meeting_id})
- Einfaches Formular: Name eingeben
- "Join Meeting" Button
- Direkt in den Videocall

## Technische Details

### Meeting-ID Format
- Format: `xxx-xxxx-xxx` (z.B. `abc-defg-hij`)
- Zufällig generiert
- Leicht zu teilen und einzugeben

### Sicherheit
- Meetings laufen 24 Stunden
- Automatisches Cleanup nach Ablauf
- Keine Benutzerdaten werden gespeichert
- Verschlüsselte Verbindungen

### Vereinfachungen
- Keine Benutzerkonten
- Keine Raumverwaltung
- Keine komplexen Berechtigungen
- Fokus auf Einfachheit

## Migration vom alten System

Das alte System mit Authentifizierung bleibt unter `/app/*` verfügbar:
- `/app/login` - Login für registrierte Benutzer
- `/app/dashboard` - Dashboard für Raumverwaltung
- `/app/rooms/*` - Erweiterte Raumfunktionen

Das neue System läuft parallel unter:
- `/` - Homepage
- `/meeting/*` - Vereinfachte Meetings

## Umgebungsvariablen

Fügen Sie diese zur `.env` hinzu:
```
FRONTEND_URL=http://localhost:3000
```

## Entwicklung

1. Backend starten:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

2. Frontend starten:
```bash
cd frontend/heydok-video-frontend
npm start
```

3. Meeting erstellen:
- Öffnen Sie http://localhost:3000
- Klicken Sie auf "Start a new meeting"
- Teilen Sie den generierten Link 