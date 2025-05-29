# Simple Meet - Video Konferenz Platform

Eine vollständige Video-Meeting-Lösung im Google Meet Stil mit WebRTC-Technologie.

## ✅ Implementierte Funktionen

### Core Meeting Funktionalität
- **Meeting-Erstellung**: Automatische Generierung eindeutiger Meeting-IDs
- **Link-Sharing**: Teilbare Meeting-Links für einfachen Beitritt
- **Multi-User Support**: Mehrere Teilnehmer können gleichzeitig beitreten
- **Real-time Communication**: WebRTC für direkte Peer-to-Peer Verbindungen

### Video & Audio Features
- **HD Video Streaming**: Hochqualitative Videoübertragung
- **Audio Communication**: Kristallklare Audioqualität
- **Mute Controls**: Ein/Ausschalten von Mikrofon und Kamera
- **Responsive Layout**: Automatische Anpassung an Teilnehmerzahl

### UI/UX (Google Meet Style)
- **Adaptive Layouts**:
  - 1 Teilnehmer: Vollbild-Ansicht
  - 2 Teilnehmer: Geteilte Ansicht (50/50)
  - 3+ Teilnehmer: Hauptansicht + Sidebar mit anderen Teilnehmern
- **Control Bar**: Intuitive Bedienelemente am unteren Rand
- **Participant Counter**: Anzeige der aktuellen Teilnehmerzahl
- **Name Display**: Teilnehmernamen werden in den Video-Tiles angezeigt

### Technical Stack
- **Frontend**: React + Vite + Material-UI
- **Backend**: Node.js + Express + Socket.io
- **WebRTC**: Peer-to-Peer Video/Audio Kommunikation
- **Real-time**: Socket.io für Signaling und Presence

## 🚀 Deployment

### Lokale Entwicklung
```bash
# Backend starten (Port 5001)
cd simple-meet/backend
npm install
npm start

# Frontend starten (Port 3001)
cd simple-meet/frontend
npm install
npm run dev
```

### Heroku Deployment
Die Anwendung ist für Heroku konfiguriert und kann direkt deployed werden.

## 📱 Nutzung

1. **Meeting erstellen**: Auf der Startseite "Neues Meeting starten" klicken
2. **Link teilen**: Die generierte Meeting-URL mit anderen Teilnehmern teilen
3. **Beitreten**: Namen eingeben und dem Meeting beitreten
4. **Video-Chat**: Sofortige Video- und Audiokommunikation mit allen Teilnehmern

## 🔧 Konfiguration

### Environment Variables
```bash
# Frontend (.env)
VITE_SOCKET_SERVER=http://localhost:5001
VITE_API_BASE_URL=http://localhost:5001

# Backend
PORT=5001
FRONTEND_URL=http://localhost:3001
```

## 🎯 Nächste Schritte

- [ ] Screen Sharing Funktionalität
- [ ] Chat-System
- [ ] Meeting-Aufzeichnung
- [ ] Warteraum-Feature
- [ ] Mobile App Optimierung

---

**Status**: ✅ Vollständig funktionsfähig - Ready for Production Testing 