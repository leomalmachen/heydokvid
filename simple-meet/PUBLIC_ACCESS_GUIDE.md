# 🌐 Simple Meet - Öffentlicher Zugriff Guide

## Schnellstart (Empfohlen)

### Option 1: Localtunnel (Einfachste Methode)

```bash
# Einfach ausführen:
./start-tunnel.sh
```

Das Skript:
- Installiert automatisch localtunnel
- Startet Backend und Frontend
- Erstellt öffentliche URLs für beide
- Zeigt die URLs zum Teilen an

**Hinweis**: Bei localtunnel müssen Besucher einmal auf "Continue" klicken.

### Option 2: ngrok (Stabiler)

1. **ngrok installieren**:
   - macOS: `brew install ngrok/ngrok/ngrok`
   - Oder von https://ngrok.com/download

2. **ngrok Account erstellen** (kostenlos):
   - Registrieren auf https://ngrok.com
   - Auth Token kopieren von https://dashboard.ngrok.com/auth

3. **Auth Token setzen**:
   ```bash
   ngrok authtoken YOUR_AUTH_TOKEN
   ```

4. **Simple Meet mit ngrok starten**:
   ```bash
   ./start-public.sh
   ```

## Manuelle Methode

Falls die Skripte nicht funktionieren:

### Terminal 1 - Backend:
```bash
cd simple-meet/backend
npm install
PORT=5001 npm start
```

### Terminal 2 - Backend Tunnel:
```bash
# Mit ngrok:
ngrok http 5001

# Oder mit localtunnel:
lt --port 5001
```

Kopieren Sie die URL (z.B. `https://abc123.ngrok-free.app`)

### Terminal 3 - Frontend mit Backend URL:
```bash
cd simple-meet/frontend
npm install

# Setzen Sie die Backend URL:
echo "VITE_SOCKET_SERVER=https://abc123.ngrok-free.app" > .env.local

npm run dev
```

### Terminal 4 - Frontend Tunnel:
```bash
# Mit ngrok:
ngrok http 3000

# Oder mit localtunnel:
lt --port 3000
```

## Deployment für dauerhaften Zugriff

### Render.com + Netlify (Kostenlos)

1. **Code zu GitHub pushen**

2. **Backend auf Render.com**:
   - Neuen Web Service erstellen
   - GitHub Repo verbinden
   - Build Command: `cd simple-meet/backend && npm install`
   - Start Command: `cd simple-meet/backend && npm start`
   - Environment Variable: `FRONTEND_URL` = `https://your-app.netlify.app`

3. **Frontend auf Netlify**:
   - Neue Site von Git erstellen
   - Build Command: `cd simple-meet/frontend && npm install && npm run build`
   - Publish Directory: `simple-meet/frontend/dist`
   - Environment Variable: `VITE_SOCKET_SERVER` = `https://your-backend.onrender.com`

### Railway.app (Einfach, $5/Monat)

1. **Railway Account erstellen**
2. **Neues Projekt von GitHub**
3. **Backend Service hinzufügen**:
   - Root Directory: `/simple-meet/backend`
   - Umgebungsvariable: `FRONTEND_URL`
4. **Frontend Service hinzufügen**:
   - Root Directory: `/simple-meet/frontend`
   - Umgebungsvariable: `VITE_SOCKET_SERVER`

## Troubleshooting

### "Port bereits belegt"
```bash
# Prozesse beenden:
pkill -f "node.*simple-meet"
pkill -f "ngrok"
pkill -f "lt.*--port"
```

### ngrok Limits
- Kostenloser Plan: 1 Tunnel gleichzeitig
- Lösung: Nutzen Sie localtunnel oder upgraden Sie ngrok

### CORS Fehler
- Stellen Sie sicher, dass die Backend URL in der Frontend .env.local korrekt ist
- Backend muss die Frontend URL in CORS erlauben

### WebRTC funktioniert nicht
- HTTPS ist erforderlich (automatisch bei ngrok/localtunnel)
- Firewall-Einstellungen prüfen
- Browser-Berechtigungen für Kamera/Mikrofon prüfen

## Sicherheitshinweise

- Die kostenlosen Tunnel-Services sind für Tests gedacht
- Für Produktion nutzen Sie proper Hosting (Render, Railway, etc.)
- Ändern Sie regelmäßig die Tunnel-URLs bei sensiblen Meetings 