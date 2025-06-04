# HeyDok Video - External API Documentation

## Overview

The HeyDok Video platform provides external API endpoints for integrating video meeting functionality into third-party systems. This API allows you to programmatically create meeting links and track patient status.

**Base URL:** `https://heyvid-66c7325ed29b.herokuapp.com`

**API Version:** 1.0.0

## Authentication

Currently, no authentication is required for these endpoints. In production, implement proper API key authentication.

## Endpoints

### 1. Create Meeting Link

Creates a new video meeting link that can be shared with patients.

**Endpoint:** `POST /api/external/create-meeting-link`

#### Request Body

```json
{
  "doctor_name": "Dr. Schmidt",
  "external_id": "appointment-12345" // optional
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doctor_name` | string | Yes | Name of the doctor (1-100 characters) |
| `external_id` | string | No | External identifier for tracking (max 50 characters) |

#### Response

```json
{
  "meeting_id": "abc-1234-def",
  "doctor_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/meeting/abc-1234-def?role=doctor&direct=true",
  "patient_join_url": "https://heyvid-66c7325ed29b.herokuapp.com/patient-setup?meeting=abc-1234-def",
  "external_id": "appointment-12345",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `meeting_id` | string | Unique meeting identifier |
| `doctor_join_url` | string | Direct URL for doctor to join the meeting |
| `patient_join_url` | string | URL for patients (includes setup flow) |
| `external_id` | string | External identifier if provided |
| `created_at` | string | Meeting creation timestamp (ISO 8601) |
| `expires_at` | string | Meeting expiration timestamp (ISO 8601) |

#### Example Usage

```bash
curl -X POST "https://heyvid-66c7325ed29b.herokuapp.com/api/external/create-meeting-link" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_name": "Dr. Schmidt",
    "external_id": "appointment-12345"
  }'
```

```python
import requests

response = requests.post(
    "https://heyvid-66c7325ed29b.herokuapp.com/api/external/create-meeting-link",
    json={
        "doctor_name": "Dr. Schmidt",
        "external_id": "appointment-12345"
    }
)
meeting_data = response.json()
print(f"Patient Link: {meeting_data['patient_join_url']}")
```

### 2. Update Patient Status

Updates the patient status for tracking purposes during the meeting lifecycle.

**Endpoint:** `POST /api/external/patient-status`

#### Request Body

```json
{
  "meeting_id": "abc-1234-def",
  "patient_name": "Max Mustermann",
  "status": "in_meeting",
  "timestamp": "2024-01-15T10:35:00Z" // optional
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `meeting_id` | string | Yes | Meeting identifier |
| `patient_name` | string | No | Patient name (max 100 characters) |
| `status` | string | Yes | Patient status (see values below) |
| `timestamp` | string | No | Timestamp of status change (ISO 8601) |

#### Status Values

| Status | Description |
|--------|-------------|
| `joining` | Patient is joining the meeting (setup completed) |
| `in_meeting` | Patient is currently in the meeting |
| `left` | Patient has left the meeting |
| `setup_incomplete` | Patient setup is not completed |

#### Response

```json
{
  "meeting_id": "abc-1234-def",
  "patient_name": "Max Mustermann",
  "status": "in_meeting",
  "updated_at": "2024-01-15T10:35:00Z",
  "success": true
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `meeting_id` | string | Meeting identifier |
| `patient_name` | string | Patient name |
| `status` | string | Updated patient status |
| `updated_at` | string | Update timestamp (ISO 8601) |
| `success` | boolean | Operation success indicator |

#### Example Usage

```bash
curl -X POST "https://heyvid-66c7325ed29b.herokuapp.com/api/external/patient-status" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "abc-1234-def",
    "patient_name": "Max Mustermann",
    "status": "in_meeting"
  }'
```

```python
import requests

response = requests.post(
    "https://heyvid-66c7325ed29b.herokuapp.com/api/external/patient-status",
    json={
        "meeting_id": "abc-1234-def",
        "patient_name": "Max Mustermann",
        "status": "in_meeting"
    }
)
status_update = response.json()
print(f"Status updated: {status_update['success']}")
```

## Integration Workflow

### Basic Integration Flow

1. **Create Meeting Link**
   ```
   POST /api/external/create-meeting-link
   ```
   - Creates meeting and returns URLs
   - Send `patient_join_url` to patient
   - Doctor uses `doctor_join_url` to join directly

2. **Track Patient Status** (Optional)
   ```
   POST /api/external/patient-status
   ```
   - Update status as patient progresses through setup
   - Track when patient joins/leaves meeting

### Example Integration

```python
import requests
import time

class HeyDokAPI:
    def __init__(self, base_url="https://heyvid-66c7325ed29b.herokuapp.com"):
        self.base_url = base_url
    
    def create_meeting(self, doctor_name, external_id=None):
        """Create a new meeting link"""
        response = requests.post(
            f"{self.base_url}/api/external/create-meeting-link",
            json={
                "doctor_name": doctor_name,
                "external_id": external_id
            }
        )
        response.raise_for_status()
        return response.json()
    
    def update_patient_status(self, meeting_id, status, patient_name=None):
        """Update patient status"""
        response = requests.post(
            f"{self.base_url}/api/external/patient-status",
            json={
                "meeting_id": meeting_id,
                "patient_name": patient_name,
                "status": status
            }
        )
        response.raise_for_status()
        return response.json()

# Usage example
api = HeyDokAPI()

# Create meeting
meeting = api.create_meeting("Dr. Schmidt", "appointment-12345")
print(f"Patient URL: {meeting['patient_join_url']}")

# Update status when patient joins
api.update_patient_status(
    meeting_id=meeting['meeting_id'],
    status="in_meeting",
    patient_name="Max Mustermann"
)
```

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Meeting not found |
| 422 | Validation Error - Invalid request format |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Rate Limits

Currently no rate limits are implemented. In production, implement appropriate rate limiting.

## Swagger Documentation

Interactive API documentation is available at:
`https://heyvid-66c7325ed29b.herokuapp.com/docs`

## Support

For technical support or questions about the API, please contact the development team.

## Changelog

### Version 1.0.0
- Initial release
- Create meeting link endpoint
- Patient status update endpoint 