# 🚀 Schnelltest-Anleitung: Meeting-Links mit mehreren Personen testen

## Option 1: Ngrok (Sofort testen - 5 Minuten)

### Schritt 1: Ngrok installieren
```bash
# macOS
brew install ngrok/ngrok/ngrok

# Oder download von https://ngrok.com/download
```

### Schritt 2: Ngrok Account & Auth Token
1. Erstelle kostenlosen Account auf https://ngrok.com
2. Kopiere deinen Auth Token von https://dashboard.ngrok.com/get-started/your-authtoken
3. Setze den Token:
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Schritt 3: Backend & Frontend starten
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend/heydok-video-frontend
npm start
```

### Schritt 4: Ngrok Tunnel starten
```bash
# Terminal 3: Ngrok für beide Services
ngrok start --all
```

Ngrok Config (ngrok.yml):
```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  frontend:
    addr: 3000
    proto: http
  backend:
    addr: 8000
    proto: http
```

### Schritt 5: Frontend konfigurieren
1. Kopiere die Backend-URL von Ngrok (z.B. https://abc123.ngrok.io)
2. Update `frontend/heydok-video-frontend/src/services/api.ts`:
   - Ändere `API_BASE_URL` zu deiner Ngrok Backend URL

### Schritt 6: CORS im Backend anpassen
Update `backend/app/core/config.py`:
- Füge deine Ngrok Frontend URL zu CORS_ORIGINS hinzu

### Schritt 7: Testen!
1. Öffne die Ngrok Frontend URL
2. Erstelle ein Meeting
3. Teile den Link mit anderen
4. Teste mit mehreren Geräten/Browsern

## Option 2: Render.com + Netlify (Stabiler - 30 Minuten)

### Backend auf Render.com
1. Push Code zu GitHub
2. Gehe zu https://render.com
3. New → Blueprint → Wähle dein Repo
4. Wähle `render.yaml`
5. Deploy startet automatisch

### Frontend auf Netlify
1. Nach Backend-Deploy: Kopiere Backend URL
2. Update `.env.production` mit Backend URL
3. Build Frontend:
   ```bash
   cd frontend/heydok-video-frontend
   npm run build
   ```
4. Gehe zu https://netlify.com
5. Drag & Drop `build` Ordner
6. Fertig!

### CORS Update
Nach beiden Deployments:
1. Update CORS_ORIGINS im Render Dashboard
2. Füge Netlify URL hinzu

## 🎯 Test-Checkliste

- [ ] Meeting erstellen funktioniert
- [ ] Link kann geteilt werden
- [ ] Zweite Person kann beitreten
- [ ] Video/Audio funktioniert für beide
- [ ] Screensharing funktioniert
- [ ] Beide sehen sich gegenseitig
- [ ] Meeting verlassen funktioniert

## 🔥 Troubleshooting

### "CORS Error"
- Backend CORS_ORIGINS prüfen
- Ngrok URLs korrekt eingetragen?

### "Connection Failed"
- LiveKit Credentials korrekt?
- Firewall/VPN deaktiviert?

### "Meeting not found"
- Backend läuft?
- API URL korrekt konfiguriert?

## 📱 Mobile Testing
- Ngrok URLs funktionieren auf Smartphones
- QR Code Generator für einfaches Teilen
- Chrome/Safari auf iOS/Android testen 