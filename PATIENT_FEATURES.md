# Patient Pre-Meeting Features

## Übersicht

Das HeyDok Video-System wurde erweitert um spezielle Features für Arzt-Patient Sprechstunden:

### 1. Patient Setup Prozess

Der Patient durchläuft vor dem Meeting-Beitritt einen mehrstufigen Setup-Prozess:

#### Schritt 1: Patienteninformationen
- Eingabe des Patientennamens
- Validierung der Eingabe

#### Schritt 2: Dokumenten-Upload
- Upload von Krankenkassenschein oder anderen relevanten Dokumenten
- Unterstützte Formate: PDF, JPG, PNG, DOC, DOCX
- Maximale Dateigröße: 10MB
- Drag & Drop Funktionalität
- Automatische Dokumentenverarbeitung über POST API

#### Schritt 3: Media-Test
- Kamera-Test mit Live-Vorschau
- Mikrofon-Test mit Audio-Level Anzeige
- Bestätigungsboxen für funktionierende Hardware
- Nur bei erfolgreicher Bestätigung ist Meeting-Beitritt möglich

#### Schritt 4: Meeting-Beitritt
- Finale Bestätigung und automatische Weiterleitung ins Meeting

## API Endpunkte

### Document Upload
```
POST /api/meetings/{meeting_id}/upload-document
Content-Type: multipart/form-data

Body:
- file: UploadFile
- patient_name: str

Response: DocumentUploadResponse
```

### Document Processing
```
POST /api/meetings/{meeting_id}/process-document
Content-Type: application/x-www-form-urlencoded

Body:
- document_id: str

Response: Processing result with extracted data
```

### Media Test
```
POST /api/meetings/{meeting_id}/media-test
Content-Type: application/json

Body: MediaTestRequest
{
  "meeting_id": str,
  "has_camera": bool,
  "has_microphone": bool,
  "camera_working": bool,
  "microphone_working": bool,
  "patient_confirmed": bool
}

Response: MediaTestResponse
```

### Patient Join Meeting
```
POST /api/meetings/{meeting_id}/join-patient
Content-Type: application/json

Body: PatientJoinRequest
{
  "patient_name": str,
  "document_id": str (optional),
  "media_test_id": str (required)
}

Response: MeetingResponse with meeting access token
```

## Patient Setup Seite

Zugriff über: `/patient-setup?meeting={meeting_id}`

### Features:
- Responsive Design für Desktop und Mobile
- Schritt-für-Schritt Validierung
- Real-time Media-Testing
- File Upload mit Drag & Drop
- Status-Anzeigen und Fehlerbehandlung
- Audio-Level Visualization
- Automatische Navigation zwischen Schritten

## Sicherheit & Validierung

### Document Upload:
- Dateitype-Validierung
- Größenbeschränkung (10MB)
- Eindeutige Document-IDs
- Automatische Cleanup nach 24h

### Media Testing:
- Browser-native MediaDevices API
- Real-time Audio-Analysis
- User-Bestätigung erforderlich
- Test-Ergebnisse werden validiert

### Meeting Access:
- Media-Test muss bestanden werden
- Dokument-Upload optional aber empfohlen
- Eindeutige Patient-IDs pro Meeting
- Token-basierte Authentifizierung

## Technische Implementation

### Backend (FastAPI):
- Neue Pydantic Models für Validierung
- In-Memory Storage für Development
- File Upload Handling
- Media Test Validation
- Automatic Cleanup System

### Frontend (Vanilla JS):
- WebRTC MediaDevices API
- Fetch API für Server-Kommunikation
- Progressive Enhancement
- Error Handling & User Feedback
- Audio Context für Mikrofon-Level

### Storage:
- In-Memory für Development
- Produktions-Empfehlung: Redis/Database + Cloud Storage

## Deployment Hinweise

1. Upload-Ordner erstellen: `mkdir uploads`
2. Environment Variables für Production Storage
3. CORS Konfiguration für Patient-Domain
4. File Size Limits in Web Server (nginx/apache)
5. Clean-up Cronjob für persistent storage

## Verwendung

1. Arzt erstellt Meeting über bestehende API
2. Patient erhält Link zur Setup-Seite: `/patient-setup?meeting={meeting_id}`
3. Patient durchläuft Setup-Prozess
4. Bei erfolgreichem Setup automatische Weiterleitung ins Meeting
5. Meeting läuft mit normaler LiveKit-Funktionalität

## Anpassungen

- Document Processing Logic in `process_patient_document()`
- Media Test Kriterien in `submit_media_test()`
- UI/UX in `patient_setup.html`
- File Storage Backend in Upload-Endpunkten 