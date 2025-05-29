# Video Meeting System - Vollständige Implementierung

## 🎯 Überblick

Dieses System implementiert ein vollständig funktionierendes Video-Meeting-System mit LiveKit, das Google Meet ähnelt. Es ermöglicht das Erstellen von Meetings, das Teilen von Links und das Beitreten mehrerer Teilnehmer.

## ✨ Hauptfunktionen

### ✅ Meeting-Erstellung
- Generiert eindeutige Meeting-IDs im Format `xxx-xxxx-xxx`
- Erstellt persistente Räume auf dem LiveKit-Server
- Speichert Meeting-Daten in der Datenbank
- Generiert teilbare Meeting-URLs

### ✅ Teilbare Links
- Format: `https://domain.com/meeting/[MEETING-ID]`
- Jeder mit dem Link kann dem Meeting beitreten
- Automatische Weiterleitung zur Meeting-Seite

### ✅ LiveKit-Integration
- Korrekte Raum-Erstellung auf dem LiveKit-Server
- Token-Generierung für jeden Teilnehmer
- Berechtigungen für Video, Audio und Bildschirmfreigabe
- Automatische Raum-Bereinigung

### ✅ Robuste Fehlerbehandlung
- Überprüfung der Meeting-Existenz
- Behandlung von Verbindungsfehlern
- Aussagekräftige Fehlermeldungen
- Logging für Debugging

## 🏗️ Architektur

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── meetings.py          # Meeting-API-Endpoints
│   ├── core/
│   │   ├── livekit.py          # LiveKit-Client
│   │   ├── config.py           # Konfiguration
│   │   └── logging.py          # Logging
│   ├── models/
│   │   └── room.py             # Datenbank-Modelle
│   ├── schemas/
│   │   └── meeting.py          # API-Schemas
│   └── main.py                 # FastAPI-Anwendung
├── main.py                     # Entry Point
├── test_meeting_system.py      # Test-Suite
└── start_meeting_system.py     # Start-Script
```

## 🚀 Installation & Setup

### 1. Abhängigkeiten installieren
```bash
cd backend
pip install -r requirements.txt
```

### 2. Umgebungsvariablen konfigurieren
Erstellen Sie eine `.env` Datei:

```env
# Datenbank
DATABASE_URL=postgresql://user:password@localhost/heydok_video
REDIS_URL=redis://localhost:6379

# LiveKit Konfiguration
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_URL=wss://your-livekit-server.com

# Sicherheit
SECRET_KEY=your_secret_key_32_chars_minimum
JWT_SECRET=your_jwt_secret_32_chars_minimum
ENCRYPTION_KEY=your_encryption_key_32_chars_minimum

# Frontend
FRONTEND_URL=http://localhost:3000

# Optional
DEBUG=true
LOG_LEVEL=info
```

### 3. System starten
```bash
# Mit Start-Script (empfohlen)
python start_meeting_system.py

# Oder direkt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

### Automatische Tests ausführen
```bash
python test_meeting_system.py
```

### Manuelle Tests
1. **Meeting erstellen:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/meetings/create \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Meeting"}'
   ```

2. **Meeting beitreten:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/meetings/[MEETING-ID]/join \
     -H "Content-Type: application/json" \
     -d '{"display_name": "Test User"}'
   ```

## 📡 API-Endpoints

### Meeting erstellen
```http
POST /api/v1/meetings/create
Content-Type: application/json

{
  "name": "Mein Meeting"  // optional
}
```

**Response:**
```json
{
  "meeting_id": "abc-defg-hij",
  "meeting_url": "https://domain.com/meeting/abc-defg-hij",
  "created_at": "2024-01-01T12:00:00Z",
  "expires_at": "2024-01-02T12:00:00Z"
}
```

### Meeting beitreten
```http
POST /api/v1/meetings/{meeting_id}/join
Content-Type: application/json

{
  "display_name": "Max Mustermann"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "meeting_id": "abc-defg-hij",
  "livekit_url": "wss://your-livekit-server.com",
  "participant_id": "guest-12345678"
}
```

### Meeting-Info abrufen
```http
GET /api/v1/meetings/{meeting_id}/info
```

### Meeting-Existenz prüfen
```http
GET /api/v1/meetings/{meeting_id}/exists
```

### Meeting beenden
```http
DELETE /api/v1/meetings/{meeting_id}
```

## 🔧 Konfiguration

### LiveKit-Server Setup
1. **LiveKit Cloud:** Registrieren Sie sich bei [LiveKit Cloud](https://cloud.livekit.io)
2. **Self-Hosted:** Folgen Sie der [LiveKit-Dokumentation](https://docs.livekit.io/deploy/)

### Datenbank Setup
```sql
-- PostgreSQL Beispiel
CREATE DATABASE heydok_video;
CREATE USER heydok_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE heydok_video TO heydok_user;
```

### Redis Setup
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis
```

## 🔍 Debugging

### Logs überprüfen
```bash
# Logs in Echtzeit anzeigen
tail -f logs/app.log

# Spezifische Meeting-ID suchen
grep "meeting_id=abc-defg-hij" logs/app.log
```

### Häufige Probleme

1. **"Meeting not found"**
   - Überprüfen Sie die Meeting-ID
   - Prüfen Sie die Datenbankverbindung

2. **"Failed to create meeting room"**
   - Überprüfen Sie LiveKit-Konfiguration
   - Prüfen Sie Netzwerkverbindung zu LiveKit

3. **"Failed to generate access token"**
   - Überprüfen Sie LiveKit API-Schlüssel
   - Prüfen Sie Token-Berechtigungen

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "start_meeting_system.py"]
```

### Heroku
```bash
# Heroku CLI installieren und einloggen
heroku create your-app-name
heroku config:set DATABASE_URL=your_database_url
heroku config:set LIVEKIT_API_KEY=your_api_key
# ... weitere Umgebungsvariablen
git push heroku main
```

## 🔐 Sicherheit

### Produktions-Checkliste
- [ ] Sichere Umgebungsvariablen verwenden
- [ ] HTTPS aktivieren
- [ ] CORS richtig konfigurieren
- [ ] Rate Limiting aktivieren
- [ ] Logging für Audit-Zwecke
- [ ] Regelmäßige Backups

## 📊 Monitoring

### Health Check
```http
GET /health
```

### Metriken
- Aktive Meetings
- Teilnehmer-Anzahl
- Server-Status
- LiveKit-Verbindung

## 🤝 Beitragen

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Ihre Änderungen
4. Führen Sie Tests aus
5. Erstellen Sie einen Pull Request

## 📝 Changelog

### Version 2.0.0 (Aktuell)
- ✅ Vollständige LiveKit-Integration
- ✅ Persistente Raum-Erstellung
- ✅ Robuste Token-Generierung
- ✅ Umfassende Fehlerbehandlung
- ✅ Strukturierte API-Architektur
- ✅ Automatisierte Tests
- ✅ Bereinigung von Duplikaten

### Version 1.0.0
- Basis-Meeting-Funktionalität
- Einfache Token-Generierung
- In-Memory-Storage

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Logs
2. Führen Sie die Test-Suite aus
3. Konsultieren Sie die LiveKit-Dokumentation
4. Erstellen Sie ein GitHub-Issue

## 📄 Lizenz

MIT License - siehe LICENSE-Datei für Details. 