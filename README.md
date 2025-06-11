# HeyDoc Video - Telemedizin Platform

Eine moderne, sichere Video-Plattform für Telemedizin mit integriertem Patient-Setup und Dokumentenverwaltung.

## 🚀 Features

- **Video-Meetings**: Sichere, verschlüsselte Video-Kommunikation
- **Patient-Setup**: Automatisierter Onboarding-Prozess
- **Dokumentenupload**: Sichere Übertragung medizinischer Dokumente
- **Media-Tests**: Automatische Überprüfung von Kamera/Mikrofon
- **Krankenkassenkarten-OCR**: Automatische Erkennung und Datenextraktion ✨
- **Responsive Design**: Optimiert für Desktop und Mobile

## 📋 System-Anforderungen

### Python Dependencies
```bash
pip install -r requirements.txt
```

### OCR-System (für Krankenkassenkarten-Erkennung)

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
1. Download Tesseract installer from: https://tesseract-ocr.github.io/tessdoc/Installation.html
2. Install with German language pack
3. Add Tesseract to PATH

**Docker:**
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*
```

### Konfiguration

Erstellen Sie eine `.env` Datei basierend auf `env.example`:

```bash
cp env.example .env
```

## 🔧 Installation & Start

1. **Repository klonen:**
```bash
git clone <repository-url>
cd telemedizintool
```

2. **Virtual Environment erstellen:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder
.venv\Scripts\activate     # Windows
```

3. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

4. **Tesseract OCR installieren** (siehe oben)

5. **Environment konfigurieren:**
```bash
cp env.example .env
# .env Datei entsprechend anpassen
```

6. **Anwendung starten:**
```bash
python main.py
```

## 📱 Nutzung

### Arzt-Workflow:
1. Meeting erstellen über Homepage
2. Patient-Link an Patient senden
3. Direkt beitreten wenn Patient fertig ist

### Patient-Workflow:
1. Patient-Setup Link öffnen
2. **Krankenkassenkarte scannen** (automatische OCR-Erkennung) ✨
3. Zusätzliche Dokumente hochladen
4. Media-Test durchführen
5. Meeting beitreten

## 🔍 OCR-Funktionalität

Die integrierte OCR-Erkennung kann automatisch folgende Daten von deutschen Krankenkassenkarten extrahieren:

- **Name des Versicherten**
- **Krankenversicherungsnummer**
- **Name der Krankenkasse**
- **Gültigkeitsdatum**
- **Geburtsdatum**

### OCR-Features:
- **Bildvorverarbeitung**: Automatische Optimierung für bessere Erkennung
- **Robuste Parsing-Logic**: Speziell für deutsche Krankenkassenkarten
- **Fehlerbehandlung**: Graceful Fallbacks bei OCR-Problemen
- **Dual-Engine**: Frontend (Tesseract.js) + Backend (pytesseract) Fallback

## 🚀 Deployment

### Lokale Entwicklung:
```bash
./start_local.sh
```

### Production (Heroku):
- Automatisches Deployment via GitHub Integration
- Buildpack für Tesseract wird automatisch installiert
- Environment Variables über Heroku Dashboard konfigurieren

## 🔒 Sicherheit

- Verschlüsselte Video-Übertragung
- Sichere Token-basierte Authentifizierung  
- DSGVO-konforme Datenverarbeitung
- Automatische Session-Bereinigung

## 📊 API-Dokumentation

Nach dem Start verfügbar unter: `http://localhost:8000/docs`

## 🛠️ Technologie-Stack

- **Backend**: FastAPI, SQLAlchemy, Python 3.8+
- **Video**: LiveKit SDK
- **OCR**: Tesseract OCR, OpenCV, PIL ✨
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Deployment**: Heroku, Docker-ready

## 🆘 Troubleshooting

### OCR-Probleme:
- **"OCR-Engine nicht installiert"**: Tesseract OCR installieren (siehe oben)
- **"Kein Text erkannt"**: Bildqualität verbessern, bessere Beleuchtung
- **"Deutsche Sprache fehlt"**: `tesseract-ocr-deu` Paket installieren

### Video-Probleme:
- LiveKit-Konfiguration in `.env` prüfen
- Browser-Berechtigungen für Kamera/Mikrofon erlauben
- HTTPS für Production verwenden

## 📝 Lizenz

[Lizenz hier einfügen] 