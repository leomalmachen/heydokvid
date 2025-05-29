# Heydok LiveKit Integration - Medizinische Videocall-Lösung

## 🏥 Überblick

Diese Dokumentation beschreibt die vollständig optimierte LiveKit-Integration für heydok, eine DSGVO/HIPAA-konforme medizinische Videocall-Plattform für Arzt-Patient-Konsultationen.

## ✅ **Implementierte Verbesserungen**

### 1. **Frontend LiveKit-Integration**
- ✅ Vollständige Integration der `@livekit/components-react`
- ✅ Rollenbasierte UI-Komponenten (Arzt vs. Patient)
- ✅ Medizinisch optimierte Benutzeroberfläche
- ✅ Responsive Design für mobile Geräte
- ✅ HIPAA-konforme Chat-Funktionalität (vorbereitet)

### 2. **Backend-Sicherheit & Compliance**
- ✅ Rollenbasierte JWT-Token-Generierung
- ✅ DSGVO-konforme Audit-Logs
- ✅ Rate Limiting für API-Endpunkte
- ✅ Sichere Metadaten-Übertragung
- ✅ Verschlüsselte Benutzerdaten

### 3. **Meeting-Management**
- ✅ Sichere Meeting-ID-Generierung
- ✅ Automatische Token-Ablaufzeiten (2 Stunden)
- ✅ Teilnehmer-Kapazitätskontrolle
- ✅ Meeting-Status-Überwachung

### 4. **Recording-Funktionalität**
- ✅ Nur-Arzt-Recording-Berechtigung
- ✅ Sichere Aufzeichnungssteuerung
- ✅ Automatische Dateinamen-Generierung
- ✅ HIPAA-konforme Speicherung

## 🔧 **Technische Architektur**

### Backend (FastAPI)
```
app/
├── api/v1/endpoints/
│   ├── meetings.py          # Meeting-Management
│   └── recordings.py        # Recording-Steuerung
├── core/
│   ├── livekit.py          # LiveKit-Client
│   ├── security.py         # DSGVO/HIPAA-Sicherheit
│   └── config.py           # Konfiguration
└── models/
    └── user.py             # Benutzermodell mit Rollen
```

### Frontend (React + TypeScript)
```
src/
├── components/
│   └── VideoRoom.tsx       # Hauptkomponente für Videocalls
├── pages/
│   └── MeetingPage.tsx     # Meeting-Beitrittsseite
├── services/
│   └── api.ts              # Backend-Integration
└── styles/
    └── VideoRoom.css       # Medizinisches Design
```

## 🚀 **Join-Flow für Arzt-Patient-Meetings**

### 1. Meeting-Erstellung (Arzt)
```typescript
// API-Aufruf für Meeting-Erstellung
const response = await fetch('/api/v1/meetings/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: "Konsultation Dr. Müller",
    max_participants: 2,
    enable_recording: true,
    enable_chat: true
  })
});

const { meeting_id, meeting_link } = await response.json();
```

### 2. Meeting-Beitritt (Patient/Arzt)
```typescript
// Sicherer Beitritt mit Rollenvalidierung
const joinResponse = await fetch(`/api/v1/meetings/${meetingId}/join`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_name: "Max Mustermann",
    user_role: "patient", // oder "physician"
    enable_video: true,
    enable_audio: true
  })
});

const { token, livekit_url, permissions } = await joinResponse.json();
```

### 3. LiveKit-Room-Verbindung
```tsx
<LiveKitRoom
  token={token}
  serverUrl={livekit_url}
  options={{
    adaptiveStream: true,
    dynacast: true,
    videoCaptureDefaults: {
      resolution: { width: 1280, height: 720 },
      facingMode: 'user',
    },
    audioCaptureDefaults: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  }}
>
  <VideoConference />
  <MedicalControlBar onLeave={onLeave} />
</LiveKitRoom>
```

## 🔐 **Sicherheitsfeatures**

### DSGVO-Compliance
- **Datenminimierung**: Nur notwendige Daten werden übertragen
- **Verschlüsselung**: End-to-End-Verschlüsselung für alle Kommunikation
- **Audit-Logs**: Vollständige Nachverfolgung aller Aktionen
- **Recht auf Vergessenwerden**: Automatische Datenlöschung nach Ablauf

### HIPAA-Compliance
- **BAA-konforme Infrastruktur**: LiveKit Cloud mit HIPAA-Zertifizierung
- **Sichere Token**: JWT mit kurzen Ablaufzeiten
- **Rollenbasierte Zugriffe**: Strenge Berechtigungskontrollen
- **Sichere Aufzeichnungen**: Verschlüsselte Speicherung

### Rate Limiting
```python
@rate_limit(calls=20, period=60)  # 20 Aufrufe pro Minute
async def join_meeting(meeting_id: str, request: JoinMeetingRequest):
    # Meeting-Beitritt mit Schutz vor Missbrauch
```

## 🎯 **Rollenbasierte Berechtigungen**

### Arzt (Physician)
- ✅ Meeting erstellen und beenden
- ✅ Aufzeichnungen starten/stoppen
- ✅ Alle Teilnehmer moderieren
- ✅ Chat-Nachrichten senden/empfangen
- ✅ Bildschirm teilen

### Patient
- ✅ Meeting beitreten (nur mit gültigem Link)
- ✅ Video/Audio teilen
- ✅ Chat-Nachrichten empfangen
- ❌ Aufzeichnungen steuern
- ❌ Meeting beenden

## 📱 **Mobile Optimierung**

### Responsive Design
```css
@media (max-width: 768px) {
  .medical-control-bar {
    flex-direction: column;
    gap: 12px;
  }
  
  .control-btn {
    width: 44px;
    height: 44px;
  }
}
```

### iOS Safari Unterstützung
```tsx
{/* Automatische Audio-Aktivierung für iOS */}
<StartAudio label="Audio aktivieren" />
```

## 🔧 **Konfiguration**

### Umgebungsvariablen
```bash
# LiveKit-Konfiguration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Sicherheit
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://heydok.com,https://app.heydok.com

# Frontend
FRONTEND_URL=https://app.heydok.com
```

### LiveKit-Server-Einstellungen
```yaml
# livekit.yaml
room:
  auto_create: true
  empty_timeout: 300s
  max_participants: 10

recording:
  enabled: true
  storage:
    type: s3
    bucket: heydok-recordings
    encryption: true
```

## 🚀 **Deployment**

### Docker-Setup
```dockerfile
# Dockerfile
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
COPY --from=frontend /app/frontend/build ./static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes-Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heydok-video
spec:
  replicas: 3
  selector:
    matchLabels:
      app: heydok-video
  template:
    metadata:
      labels:
        app: heydok-video
    spec:
      containers:
      - name: heydok-video
        image: heydok/video:latest
        ports:
        - containerPort: 8000
        env:
        - name: LIVEKIT_URL
          valueFrom:
            secretKeyRef:
              name: livekit-secrets
              key: url
```

## 📊 **Monitoring & Logging**

### Strukturiertes Logging
```python
logger.info("Meeting created",
           meeting_id=meeting_id,
           created_by=current_user.id,
           max_participants=request.max_participants,
           enable_recording=request.enable_recording,
           client_ip=http_request.client.host)
```

### Metriken
- Meeting-Erstellungen pro Tag
- Durchschnittliche Meeting-Dauer
- Teilnehmeranzahl-Verteilung
- Fehlerrate bei Verbindungen

## 🧪 **Testing**

### API-Tests
```python
# test_meetings.py
async def test_create_meeting():
    response = await client.post("/api/v1/meetings/create", 
                               json={"name": "Test Meeting"})
    assert response.status_code == 200
    assert "meeting_id" in response.json()

async def test_join_meeting_with_role():
    # Test rollenbasierte Berechtigung
    response = await client.post(f"/api/v1/meetings/{meeting_id}/join",
                               json={"user_name": "Dr. Test", "user_role": "physician"})
    data = response.json()
    assert data["permissions"]["can_record"] == True
```

### Frontend-Tests
```typescript
// VideoRoom.test.tsx
describe('VideoRoom', () => {
  it('should show recording button for physicians', () => {
    const mockToken = generateMockToken({ role: 'physician' });
    render(<VideoRoom token={mockToken} {...props} />);
    expect(screen.getByTitle('Start Recording')).toBeInTheDocument();
  });
});
```

## 🔄 **Nächste Schritte**

### Kurzfristig (1-2 Wochen)
1. **Chat-Funktionalität vervollständigen**
   - Sichere Nachrichtenübertragung
   - Nachrichtenverschlüsselung
   - Chat-Historie (optional)

2. **Erweiterte Recording-Features**
   - Automatische Transkription
   - Recording-Metadaten
   - Sichere Speicherung in S3

### Mittelfristig (1-2 Monate)
1. **Erweiterte Benutzerauthentifizierung**
   - Integration mit heydok-Benutzersystem
   - Single Sign-On (SSO)
   - Multi-Faktor-Authentifizierung

2. **Analytics & Reporting**
   - Meeting-Qualitätsmetriken
   - Nutzungsstatistiken
   - DSGVO-konforme Berichte

### Langfristig (3-6 Monate)
1. **KI-Integration**
   - Automatische Zusammenfassungen
   - Symptom-Erkennung
   - Qualitätssicherung

2. **Erweiterte Collaboration**
   - Whiteboard-Funktionalität
   - Dokumenten-Sharing
   - Terminplanung-Integration

## 📞 **Support & Wartung**

### Monitoring-Alerts
- LiveKit-Server-Verfügbarkeit
- API-Response-Zeiten > 2s
- Fehlerrate > 1%
- Speicherplatz für Recordings

### Backup-Strategie
- Tägliche Datenbank-Backups
- Recording-Replikation
- Konfiguration in Git

### Sicherheitsupdates
- Monatliche Dependency-Updates
- Vierteljährliche Sicherheitsaudits
- Jährliche Penetrationstests

---

**Kontakt**: Für technische Fragen zur Integration wenden Sie sich an das Entwicklungsteam. 