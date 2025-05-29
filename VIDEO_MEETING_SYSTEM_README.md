# 🎥 Video Meeting System

Ein vollständig funktionierendes Video-Meeting-System mit LiveKit, das es Benutzern ermöglicht, sofort Meetings zu erstellen und beizutreten.

## ✨ Features

- **Einfache Meeting-Erstellung**: Geben Sie Ihren Namen ein und erstellen Sie sofort ein Meeting
- **Meeting-Beitritt**: Treten Sie bestehenden Meetings mit einer Meeting-ID bei
- **Teilbare Links**: Jedes Meeting erhält einen eindeutigen, teilbaren Link
- **Video & Audio**: Vollständige Video- und Audio-Kommunikation über LiveKit Cloud
- **Keine Registrierung**: Sofort einsatzbereit ohne Anmeldung
- **Responsive Design**: Funktioniert auf Desktop und Mobile

## 🚀 Schnellstart

### 1. System starten

```bash
./start-video-meetings.sh
```

Das System startet automatisch auf `http://localhost:8000`

### 2. Meeting erstellen

1. Öffnen Sie `http://localhost:8000` in Ihrem Browser
2. Geben Sie Ihren Namen ein
3. Klicken Sie auf "Neues Meeting erstellen"
4. Sie erhalten einen teilbaren Link wie: `http://localhost:8000/meeting/abc-1234-xyz`
5. Teilen Sie diesen Link mit anderen Teilnehmern

### 3. Meeting beitreten

**Option A: Über Link**
- Öffnen Sie den erhaltenen Meeting-Link direkt

**Option B: Über Meeting-ID**
1. Öffnen Sie `http://localhost:8000`
2. Geben Sie Ihren Namen ein
3. Klicken Sie auf "Meeting beitreten"
4. Geben Sie die Meeting-ID ein (z.B. `abc-1234-xyz`)
5. Klicken Sie auf "Meeting beitreten"

## 🛠 Technische Details

### Architektur

- **Frontend**: Vanilla HTML/CSS/JavaScript mit LiveKit Client SDK
- **Backend**: FastAPI (Python) mit LiveKit Server Integration
- **Video/Audio**: LiveKit Cloud Infrastructure
- **Routing**: `/meeting/{meeting-id}` für direkte Meeting-Links

### API Endpoints

- `GET /` - Frontend Homepage
- `POST /api/v1/meetings/create` - Neues Meeting erstellen
- `GET /api/v1/meetings/{id}/exists` - Meeting-Existenz prüfen
- `POST /api/v1/meetings/{id}/join` - Meeting beitreten
- `GET /meeting/{id}` - Meeting-Seite für spezifische ID
- `GET /health` - System-Status

### Meeting-ID Format

Meeting-IDs werden im Format `xxx-xxxx-xxx` generiert (z.B. `abc-1234-xyz`)

### Token-Generierung

Jeder Teilnehmer erhält einen eindeutigen JWT-Token mit:
- Raum-Berechtigung (roomJoin: true)
- Publish-Berechtigung (canPublish: true)
- Subscribe-Berechtigung (canSubscribe: true)
- 24-Stunden Gültigkeit

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
LIVEKIT_API_KEY=APIwkvkVSaRyTE3
LIVEKIT_API_SECRET=7FVh4h09qkZyejvgtV4Mc5Yo6uNgaMNVofxvCQBnRgf
LIVEKIT_URL=wss://google-meet-replacer-fcw5apmd.livekit.cloud
PORT=8000
```

### LiveKit Cloud

Das System verwendet LiveKit Cloud für:
- Automatische Raum-Erstellung
- Video/Audio-Streaming
- Teilnehmer-Management
- Sichere Token-Validierung

## 🎯 Verwendungsszenarien

### Szenario 1: Spontanes Meeting

1. **Nutzer A**: Öffnet `http://localhost:8000`, gibt Namen ein, erstellt Meeting
2. **System**: Generiert Link `http://localhost:8000/meeting/abc-1234-xyz`
3. **Nutzer A**: Teilt Link per Chat/E-Mail
4. **Nutzer B**: Öffnet Link, gibt Namen ein, tritt bei
5. **Beide**: Sind im selben LiveKit-Raum und können kommunizieren

### Szenario 2: Geplantes Meeting

1. **Organisator**: Erstellt Meeting im Voraus, teilt Link
2. **Teilnehmer**: Öffnen Link zur vereinbarten Zeit
3. **System**: Alle landen im selben Raum

### Szenario 3: Meeting-ID Beitritt

1. **Nutzer**: Hat nur die Meeting-ID (z.B. `abc-1234-xyz`)
2. **Nutzer**: Geht zu `http://localhost:8000`, klickt "Meeting beitreten"
3. **Nutzer**: Gibt Meeting-ID ein und tritt bei

## 🔍 Debugging

### Server-Status prüfen

```bash
curl http://localhost:8000/health
```

### Meeting erstellen (API)

```bash
curl -X POST http://localhost:8000/api/v1/meetings/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Meeting"}'
```

### Meeting-Existenz prüfen

```bash
curl http://localhost:8000/api/v1/meetings/{meeting-id}/exists
```

## 🚨 Troubleshooting

### Port bereits belegt

```bash
lsof -ti:8000 | xargs kill -9
```

### LiveKit-Verbindungsfehler

- Prüfen Sie die LiveKit-Credentials
- Stellen Sie sicher, dass die LiveKit Cloud URL erreichbar ist
- Überprüfen Sie die Netzwerk-Firewall-Einstellungen

### Frontend lädt nicht

- Prüfen Sie, ob der Server auf Port 8000 läuft
- Überprüfen Sie die Browser-Konsole auf JavaScript-Fehler

## 📱 Browser-Kompatibilität

- ✅ Chrome/Chromium (empfohlen)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

**Hinweis**: Kamera/Mikrofon-Zugriff erfordert HTTPS in Produktion oder localhost für Entwicklung.

## 🔒 Sicherheit

- Meetings laufen über sichere WebSocket-Verbindungen (WSS)
- JWT-Tokens haben begrenzte Gültigkeit (24h)
- Keine persistente Speicherung von Benutzerdaten
- LiveKit Cloud bietet Enterprise-Grade Sicherheit

## 📈 Skalierung

Das System kann erweitert werden durch:
- Datenbank für persistente Meeting-Speicherung
- Benutzer-Authentifizierung
- Meeting-Aufzeichnung
- Chat-Funktionalität
- Bildschirmfreigabe
- Mehr Teilnehmer pro Raum

---

**Entwickelt mit ❤️ für einfache Video-Kommunikation** 