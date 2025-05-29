# 🎥 Video Meeting App

Eine vollständig funktionsfähige Video-Meeting-Anwendung im Google Meet Stil, entwickelt mit LiveKit und FastAPI.

## ✨ Features

- **🚀 Sofortige Meeting-Erstellung**: Geben Sie Ihren Namen ein und erstellen Sie sofort ein Meeting
- **🔗 Teilbare Links**: Jedes Meeting erhält einen eindeutigen, teilbaren Link im Format `/meeting/{meeting-id}`
- **📱 Meeting-Beitritt**: Treten Sie Meetings über ID oder direkten Link bei
- **🎬 Video & Audio**: Vollständige Video- und Audio-Kommunikation über LiveKit Cloud
- **📱 Responsive Design**: Funktioniert auf Desktop und Mobile
- **🔒 Keine Registrierung**: Sofort einsatzbereit ohne Anmeldung

## 🚀 Schnellstart

### 1. Repository klonen

```bash
git clone https://github.com/leomalmachen/video-meeting-app.git
cd video-meeting-app
```

### 2. System starten

```bash
cd backend
./start-video-meetings.sh
```

### 3. Meeting erstellen oder beitreten

Öffnen Sie `http://localhost:8000` in Ihrem Browser:

- **Meeting erstellen**: Namen eingeben → "Neues Meeting erstellen" → Link teilen
- **Meeting beitreten**: Namen eingeben → "Meeting beitreten" → Meeting-ID eingeben

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

### Meeting-ID Format

Meeting-IDs werden im Format `xxx-xxxx-xxx` generiert (z.B. `abc-1234-xyz`)

## 🎯 Verwendungsszenarien

### Spontanes Meeting
1. **Nutzer A**: Öffnet App, gibt Namen ein, erstellt Meeting
2. **System**: Generiert Link `http://localhost:8000/meeting/abc-1234-xyz`
3. **Nutzer A**: Teilt Link per Chat/E-Mail
4. **Nutzer B**: Öffnet Link, gibt Namen ein, tritt bei
5. **Beide**: Sind im selben LiveKit-Raum und können kommunizieren

### Meeting-ID Beitritt
1. **Nutzer**: Hat Meeting-ID (z.B. `abc-1234-xyz`)
2. **Nutzer**: Geht zur App, klickt "Meeting beitreten"
3. **Nutzer**: Gibt Meeting-ID ein und tritt bei

## 📁 Projektstruktur

```
video-meeting-app/
├── backend/
│   ├── backend/
│   │   └── main.py              # FastAPI Server
│   ├── frontend/
│   │   ├── index.html           # Homepage
│   │   └── meeting.html         # Meeting Interface
│   ├── start-video-meetings.sh  # Startskript
│   ├── requirements.txt         # Python Dependencies
│   └── VIDEO_MEETING_SYSTEM_README.md
├── README.md
└── .gitignore
```

## 🔧 Entwicklung

### Voraussetzungen

- Python 3.8+
- LiveKit Cloud Account (Credentials sind bereits konfiguriert)

### Lokale Entwicklung

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/main.py
```

### Umgebungsvariablen

```bash
LIVEKIT_API_KEY=APIwkvkVSaRyTE3
LIVEKIT_API_SECRET=7FVh4h09qkZyejvgtV4Mc5Yo6uNgaMNVofxvCQBnRgf
LIVEKIT_URL=wss://google-meet-replacer-fcw5apmd.livekit.cloud
PORT=8000
```

## 🚨 Troubleshooting

### Port bereits belegt
```bash
lsof -ti:8000 | xargs kill -9
```

### LiveKit-Verbindungsfehler
- Prüfen Sie die LiveKit-Credentials
- Stellen Sie sicher, dass die LiveKit Cloud URL erreichbar ist

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

## 📈 Roadmap

- [ ] Benutzer-Authentifizierung
- [ ] Meeting-Aufzeichnung
- [ ] Chat-Funktionalität
- [ ] Bildschirmfreigabe
- [ ] Mobile Apps (iOS/Android)
- [ ] Meeting-Planung
- [ ] Mehr Teilnehmer pro Raum

## 🤝 Contributing

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.

## 📄 Lizenz

Apache 2.0 License - siehe [LICENSE](LICENSE) für Details.

## 🔗 Links

- **Live Demo**: [video-meeting-app-two.vercel.app](https://video-meeting-app-two.vercel.app)
- **GitHub**: [github.com/leomalmachen/video-meeting-app](https://github.com/leomalmachen/video-meeting-app)
- **LiveKit**: [livekit.io](https://livekit.io)

---

**Entwickelt mit ❤️ für einfache Video-Kommunikation** 