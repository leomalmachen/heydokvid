# Video Meeting Setup Guide

## Voraussetzungen

1. **LiveKit Server** muss lokal laufen
2. **Python 3.8+** für das Backend
3. **Node.js** (optional, für Entwicklung)

## LiveKit Installation und Start

### Option 1: Mit Docker (empfohlen)

```bash
# LiveKit Server starten
docker run -d \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: secret" \
  livekit/livekit-server \
  --dev \
  --node-ip=127.0.0.1
```

### Option 2: Mit Binary

```bash
# Download LiveKit
curl -sSL https://get.livekit.io | bash

# Start LiveKit
livekit-server --dev --node-ip=127.0.0.1
```

## Backend Setup

1. **Umgebungsvariablen erstellen**:

Erstelle eine `.env` Datei im Hauptverzeichnis:

```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Frontend URL
FRONTEND_URL=http://localhost:3001

# Backend Port
PORT=8001
```

2. **Backend starten**:

```bash
cd backend
python -m uvicorn simple_meetings_api:app --reload --port 8001
```

## Frontend Setup

Das Frontend wird direkt vom Backend ausgeliefert. Öffne einfach:

```
http://localhost:8001
```

## Testen der Video-Meeting-Funktionalität

1. **Meeting erstellen**:
   - Öffne http://localhost:8001
   - Klicke auf "Meeting starten"
   - Du wirst zur Meeting-Seite weitergeleitet

2. **Zweiten Teilnehmer hinzufügen**:
   - Kopiere die URL aus der Adressleiste
   - Öffne die URL in einem neuen Browser-Tab oder anderem Browser
   - Gib einen anderen Namen ein
   - Klicke auf "Meeting beitreten"

3. **Erwartetes Verhalten**:
   - Beide Teilnehmer sollten sich gegenseitig sehen
   - Das eigene Video erscheint klein unten rechts
   - Das Video des anderen Teilnehmers füllt den Hauptbereich
   - Audio und Video können ein-/ausgeschaltet werden
   - Meeting kann beendet werden

## Troubleshooting

### "Kamera/Mikrofon konnte nicht aktiviert werden"
- Stelle sicher, dass der Browser Zugriff auf Kamera und Mikrofon hat
- In Chrome: chrome://settings/content/camera und chrome://settings/content/microphone

### "Meeting-Beitritt fehlgeschlagen"
- Überprüfe, ob LiveKit läuft: `curl http://localhost:7880/health`
- Überprüfe die Backend-Logs
- Stelle sicher, dass die Ports 7880-7882 frei sind

### Teilnehmer sehen sich nicht
- Öffne die Browser-Konsole (F12) und prüfe auf Fehler
- Stelle sicher, dass beide Teilnehmer dieselbe Meeting-ID verwenden
- Überprüfe die LiveKit-Verbindung in den Logs

## Produktions-Deployment

Für Produktion benötigst du:

1. **Öffentlich erreichbaren LiveKit Server** mit SSL
2. **TURN Server** für NAT-Traversal
3. **Angepasste Umgebungsvariablen** mit echten API-Keys
4. **HTTPS** für Frontend und Backend

Siehe `DEPLOYMENT.md` für detaillierte Anweisungen. 