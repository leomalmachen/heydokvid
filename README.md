# HeyDok Video - Simple Video Meeting Platform

Eine minimale, voll funktionsfähige Video-Meeting-Plattform ähnlich wie Google Meet. Nutzer können mit einem Klick ein Meeting starten, den Link teilen, und andere können sofort beitreten - ohne Registrierung.

## 🚀 Features

- **One-Click Meeting Creation** - Kein Login erforderlich
- **Instant Join** - Mit Meeting-Code oder Link
- **Video/Audio Controls** - Mikrofon und Kamera An/Aus
- **Responsive Design** - Funktioniert auf Desktop und Mobile
- **Real-time Video** - Powered by LiveKit

## 📋 Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Video/Audio**: LiveKit WebRTC
- **Deployment**: Render.com (kostenlos)

## 🛠️ Local Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/heydokvid.git
cd heydokvid
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
Create a `.env` file in the root directory:
```env
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

⚠️ **WICHTIG**: Niemals echte API-Schlüssel in GitHub committen!

### 5. Run the Application
```bash
cd backend
uvicorn main:app --reload
```

Visit http://localhost:8000

## 🚀 Deploy to Render.com (Kostenlos)

### 1. Vorbereitung
- Erstellen Sie einen [LiveKit Cloud Account](https://livekit.io/cloud) (kostenlos)
- Forken Sie dieses Repository zu Ihrem GitHub Account

### 2. Deploy auf Render
1. Gehen Sie zu [render.com](https://render.com) und melden Sie sich mit GitHub an
2. Klicken Sie auf "New +" → "Web Service"
3. Verbinden Sie Ihr GitHub Repository
4. Render erkennt automatisch die `render.yaml` Konfiguration
5. Fügen Sie die Environment Variables hinzu:
   - `LIVEKIT_URL`: Ihre LiveKit Server URL
   - `LIVEKIT_API_KEY`: Ihr LiveKit API Key
   - `LIVEKIT_API_SECRET`: Ihr LiveKit API Secret
   - `APP_URL`: Wird automatisch gesetzt (https://ihr-app-name.onrender.com)

### 3. Deployment
- Klicken Sie auf "Create Web Service"
- Warten Sie 2-3 Minuten für das erste Deployment
- Ihre App ist live unter: `https://ihr-app-name.onrender.com`

## 📁 Project Structure

```
heydok-video/
├── backend/
│   ├── main.py           # FastAPI Server
│   └── livekit_client.py # LiveKit Integration
├── frontend/
│   ├── index.html        # Homepage
│   ├── meeting.html      # Meeting Room
│   └── app.js           # Meeting Logic
├── static/
│   └── style.css        # Styling
├── requirements.txt     # Python Dependencies
├── render.yaml         # Render.com Config
└── README.md          # This file
```

## 🔧 Development

### Testing Locally
1. Start the backend server
2. Open browser 1 and create a meeting
3. Copy the meeting link
4. Open browser 2 (or incognito) and join with the link
5. Test video/audio and controls

### Common Issues

**LiveKit Connection Failed**
- Check environment variables
- Ensure LIVEKIT_URL starts with `wss://`
- Verify API Key and Secret match

**No Video/Audio**
- HTTPS required (except localhost)
- Check browser permissions
- Look for console errors

## 🔒 Security Notes

- Verwenden Sie niemals die API-Schlüssel aus Beispielen
- Erstellen Sie eigene LiveKit Credentials
- Nutzen Sie Environment Variables für alle Secrets
- Aktivieren Sie CORS-Restrictions für Production

## 📝 License

MIT License - feel free to use this project for anything!

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 