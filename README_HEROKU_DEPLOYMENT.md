# Video Meeting Platform - Heroku Deployment

## Schnell-Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Manuelle Deployment-Schritte

### 1. Heroku CLI installieren
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Oder von https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Heroku Login
```bash
heroku login
```

### 3. App erstellen
```bash
heroku create your-video-meeting-app
```

### 4. Umgebungsvariablen setzen
```bash
# Für Demo mit LiveKit Cloud
heroku config:set LIVEKIT_URL=wss://livekit-demo.livekit.cloud
heroku config:set LIVEKIT_API_KEY=devkey
heroku config:set LIVEKIT_API_SECRET=secret

# Für Produktion mit eigenem LiveKit Server
# heroku config:set LIVEKIT_URL=wss://your-livekit-server.com
# heroku config:set LIVEKIT_API_KEY=your-api-key
# heroku config:set LIVEKIT_API_SECRET=your-api-secret
```

### 5. Code deployen
```bash
git add .
git commit -m "Deploy video meeting platform"
git push heroku main
```

### 6. App öffnen
```bash
heroku open
```

## Funktionen

- ✅ Video-Meetings erstellen und beitreten
- ✅ Eindeutige Meeting-IDs
- ✅ Google Meet-ähnliches Layout
- ✅ Mikrofon/Kamera-Steuerung
- ✅ Responsive Design
- ✅ Sichere WebRTC-Verbindungen über LiveKit

## Verwendung

1. Öffne die Heroku-App-URL
2. Klicke auf "Meeting starten"
3. Teile die Meeting-URL mit anderen Teilnehmern
4. Alle Teilnehmer landen im selben Meeting-Raum

## LiveKit Konfiguration

### Demo-Modus (Standard)
Die App verwendet standardmäßig den kostenlosen LiveKit Demo-Server. Dieser ist für Tests geeignet, aber nicht für Produktion.

### Produktions-Setup
Für Produktion sollten Sie:

1. **LiveKit Cloud Account** erstellen: https://cloud.livekit.io
2. **API Keys** generieren
3. **Umgebungsvariablen** in Heroku aktualisieren:
   ```bash
   heroku config:set LIVEKIT_URL=wss://your-project.livekit.cloud
   heroku config:set LIVEKIT_API_KEY=your-api-key
   heroku config:set LIVEKIT_API_SECRET=your-api-secret
   ```

## Troubleshooting

### "Meeting-Beitritt fehlgeschlagen"
- Überprüfen Sie die LiveKit-Konfiguration
- Stellen Sie sicher, dass die API-Keys korrekt sind

### "Kamera/Mikrofon nicht verfügbar"
- HTTPS ist erforderlich für Kamera/Mikrofon-Zugriff
- Heroku Apps haben automatisch HTTPS

### Logs anzeigen
```bash
heroku logs --tail
```

## Kosten

- **Heroku**: Basic Dyno (~$7/Monat)
- **LiveKit Cloud**: Kostenloser Tier verfügbar, dann pay-per-use
- **Gesamt**: Ab ~$7/Monat für kleine Teams

## Support

Bei Problemen:
1. Überprüfen Sie die Heroku-Logs
2. Testen Sie die LiveKit-Verbindung
3. Stellen Sie sicher, dass alle Umgebungsvariablen gesetzt sind 