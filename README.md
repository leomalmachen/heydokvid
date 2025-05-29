# 🏥 Heydok Video - DSGVO/HIPAA-konforme Videocall-Plattform

Eine professionelle, medizinische Videocall-Lösung für Arzt-Patient-Konsultationen mit LiveKit-Integration.

![Heydok Video](https://img.shields.io/badge/Status-Production%20Ready-green)
![DSGVO](https://img.shields.io/badge/DSGVO-Compliant-blue)
![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-blue)
![LiveKit](https://img.shields.io/badge/LiveKit-Integrated-orange)

## 🚀 Features

### 🎯 **Medizinische Video-Konsultationen**
- **1:1 Arzt-Patient-Meetings** mit rollenbasierten Berechtigungen
- **HD Video/Audio** mit adaptiver Qualität
- **Screensharing** für medizinische Dokumentation
- **Sichere Chat-Funktionalität** (HIPAA-konform)

### 🔐 **Sicherheit & Compliance**
- **DSGVO/HIPAA-konform** mit vollständiger Audit-Trail
- **End-to-End-Verschlüsselung** für alle Kommunikation
- **Rollenbasierte Zugriffskontrolle** (Arzt vs. Patient)
- **Rate Limiting** und DDoS-Schutz

### 📹 **Recording & Dokumentation**
- **Nur-Arzt-Recording** mit sicherer Speicherung
- **Automatische Metadaten-Generierung**
- **Verschlüsselte Aufzeichnungen** für Compliance
- **Strukturierte Audit-Logs**

### 📱 **Cross-Platform**
- **Responsive Design** für Desktop, Tablet, Mobile
- **iOS Safari Unterstützung** mit automatischer Audio-Aktivierung
- **Progressive Web App** (PWA) ready
- **Offline-Fallback** für kritische Funktionen

## 🏗️ Architektur

```
heydok-video/
├── app/                     # FastAPI Backend
│   ├── api/v1/endpoints/   # REST API Endpoints
│   ├── core/               # Core Services (LiveKit, Security)
│   ├── models/             # Database Models
│   └── schemas/            # Pydantic Schemas
├── frontend/               # React Frontend
│   └── heydok-video-frontend/
│       ├── src/components/ # React Components
│       ├── src/pages/      # Page Components
│       ├── src/services/   # API Services
│       └── src/styles/     # CSS Styles
├── infrastructure/         # Deployment Configs
├── scripts/               # Utility Scripts
└── docs/                  # Documentation
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **LiveKit** - Real-time video/audio infrastructure
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation
- **Structlog** - Structured logging
- **JWT** - Secure authentication

### Frontend
- **React 18** - Modern UI framework
- **TypeScript** - Type-safe development
- **LiveKit React Components** - Professional video UI
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **React Hot Toast** - User notifications

### Infrastructure
- **Docker** - Containerization
- **Kubernetes** - Orchestration
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **S3** - Recording storage

## 🚀 Quick Start

### 1. Repository klonen
```bash
git clone https://github.com/leomalmachen/heydokvideo.git
cd heydokvideo
```

### 2. Backend Setup
```bash
# Python Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp env.example .env
# Bearbeiten Sie .env mit Ihren LiveKit-Credentials
```

### 3. Frontend Setup
```bash
cd frontend/heydok-video-frontend
npm install
```

### 4. LiveKit Konfiguration
```bash
# In .env file:
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### 5. Anwendung starten
```bash
# Backend (Terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend/heydok-video-frontend
npm start
```

🎉 **Anwendung läuft auf:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 📋 Verwendung

### Meeting erstellen (Arzt)
```bash
curl -X POST http://localhost:8000/api/v1/meetings/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Konsultation Dr. Müller",
    "max_participants": 2,
    "enable_recording": true
  }'
```

### Meeting beitreten (Patient/Arzt)
```bash
curl -X POST http://localhost:8000/api/v1/meetings/{meeting_id}/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Max Mustermann",
    "user_role": "patient"
  }'
```

## 🧪 Testing

### Integration Tests ausführen
```bash
# Backend Tests
python test_heydok_integration.py --url http://localhost:8000

# Frontend Tests
cd frontend/heydok-video-frontend
npm test
```

### Test Coverage
```bash
# Backend Coverage
pytest --cov=app tests/

# Frontend Coverage
npm run test:coverage
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build und Start
docker-compose up --build

# Production Build
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
# Apply Kubernetes configs
kubectl apply -f infrastructure/k8s/

# Check deployment status
kubectl get pods -l app=heydok-video
```

### Cloud Deployment (Render/Vercel)
```bash
# Render deployment
./deploy-render.sh

# Environment variables setzen:
# - LIVEKIT_URL
# - LIVEKIT_API_KEY
# - LIVEKIT_API_SECRET
# - DATABASE_URL
# - REDIS_URL
```

## 🔐 Sicherheit

### DSGVO Compliance
- ✅ **Datenminimierung** - Nur notwendige Daten
- ✅ **Verschlüsselung** - End-to-End für alle Kommunikation
- ✅ **Audit-Logs** - Vollständige Nachverfolgung
- ✅ **Recht auf Vergessenwerden** - Automatische Löschung

### HIPAA Compliance
- ✅ **BAA-konforme Infrastruktur** - LiveKit Cloud
- ✅ **Sichere Token** - JWT mit kurzen Ablaufzeiten
- ✅ **Rollenbasierte Zugriffe** - Strenge Berechtigungen
- ✅ **Verschlüsselte Aufzeichnungen** - S3 mit Encryption

### Sicherheitsfeatures
- **Rate Limiting** - 20 Aufrufe/Minute
- **CORS Protection** - Konfigurierbare Origins
- **SQL Injection Protection** - SQLAlchemy ORM
- **XSS Protection** - Content Security Policy

## 📊 Monitoring

### Metriken
- Meeting-Erstellungen pro Tag
- Durchschnittliche Meeting-Dauer
- Teilnehmeranzahl-Verteilung
- API Response Times
- Fehlerrate

### Logging
```python
# Strukturierte Logs
logger.info("Meeting created",
           meeting_id=meeting_id,
           created_by=user_id,
           client_ip=request.client.host)
```

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# LiveKit Status
curl http://localhost:8000/api/v1/meetings/health
```

## 🔄 API Dokumentation

### Wichtige Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/v1/meetings/create` | POST | Meeting erstellen |
| `/api/v1/meetings/{id}/join` | POST | Meeting beitreten |
| `/api/v1/meetings/{id}/info` | GET | Meeting-Informationen |
| `/api/v1/meetings/{id}/start-recording` | POST | Recording starten |
| `/api/v1/meetings/{id}/stop-recording` | POST | Recording stoppen |

### Vollständige API-Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Changes committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request öffnen

### Development Guidelines
- **Code Style**: Black + isort für Python, Prettier für TypeScript
- **Testing**: Mindestens 80% Test Coverage
- **Documentation**: Docstrings für alle öffentlichen Funktionen
- **Security**: Alle Änderungen durch Security Review

## 📞 Support

### Technischer Support
- **Issues**: [GitHub Issues](https://github.com/leomalmachen/heydokvideo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/leomalmachen/heydokvideo/discussions)
- **Email**: support@heydok.com

### Dokumentation
- **Integration Guide**: [HEYDOK_INTEGRATION_GUIDE.md](./HEYDOK_INTEGRATION_GUIDE.md)
- **API Reference**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

## 🏆 Acknowledgments

- **LiveKit** - Für die exzellente Video-Infrastruktur
- **FastAPI** - Für das moderne Python Web Framework
- **React** - Für die leistungsstarke UI-Bibliothek
- **Heydok Team** - Für die Vision einer besseren medizinischen Kommunikation

---

**Made with ❤️ for better healthcare communication**

![Heydok](https://img.shields.io/badge/Heydok-Medical%20Video%20Platform-blue?style=for-the-badge) 