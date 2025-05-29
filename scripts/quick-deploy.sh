#!/bin/bash

# Quick Deploy Script für Heydok Video Platform
# Dieses Script hilft beim schnellen Deployment für Testing

echo "🚀 Heydok Video Quick Deploy Script"
echo "=================================="

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Schritt 1: Environment Check
echo -e "\n${YELLOW}Schritt 1: Environment Check${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production nicht gefunden!${NC}"
    echo "Bitte erstelle .env.production aus env.production.example"
    exit 1
fi

if [ ! -f "frontend/heydok-video-frontend/.env.production" ]; then
    echo -e "${RED}❌ frontend/.env.production nicht gefunden!${NC}"
    echo "Bitte erstelle frontend/heydok-video-frontend/.env.production"
    exit 1
fi

echo -e "${GREEN}✅ Environment Dateien gefunden${NC}"

# Schritt 2: Security Keys generieren
echo -e "\n${YELLOW}Schritt 2: Security Keys${NC}"
echo "Generiere sichere Keys mit:"
echo "openssl rand -base64 32"
echo -e "${YELLOW}Hast du die Keys in .env.production aktualisiert? (y/n)${NC}"
read -r response
if [[ "$response" != "y" ]]; then
    echo "Bitte aktualisiere die Security Keys!"
    exit 1
fi

# Schritt 3: Deployment Optionen
echo -e "\n${YELLOW}Schritt 3: Wähle Deployment Option${NC}"
echo "1) Render.com (Empfohlen für schnelles Testing)"
echo "2) Ngrok (Nur für kurzes Testing)"
echo "3) Manual Deploy Guide"
read -p "Option (1-3): " option

case $option in
    1)
        echo -e "\n${GREEN}Render.com Deployment${NC}"
        echo "1. Gehe zu https://render.com und erstelle einen Account"
        echo "2. Klicke auf 'New +' → 'Blueprint'"
        echo "3. Verbinde dein GitHub Repository"
        echo "4. Wähle die render.yaml Datei"
        echo "5. Render erstellt automatisch:"
        echo "   - Backend Service"
        echo "   - PostgreSQL Database"
        echo "   - Redis Instance"
        echo ""
        echo "6. Nach dem Backend-Deployment:"
        echo "   - Kopiere die Backend URL (z.B. https://heydok-video-backend.onrender.com)"
        echo "   - Update frontend/.env.production mit der Backend URL"
        echo ""
        echo "7. Frontend auf Netlify deployen:"
        echo "   - Gehe zu https://netlify.com"
        echo "   - Drag & Drop den 'build' Ordner nach 'npm run build'"
        echo "   - Oder verbinde GitHub für automatisches Deployment"
        ;;
    
    2)
        echo -e "\n${GREEN}Ngrok Quick Test${NC}"
        echo "Starte Backend und Frontend lokal:"
        echo ""
        echo "Terminal 1 (Backend):"
        echo "cd backend && python -m uvicorn app.main:app --reload --port 8000"
        echo ""
        echo "Terminal 2 (Frontend):"
        echo "cd frontend/heydok-video-frontend && npm start"
        echo ""
        echo "Terminal 3 (Ngrok):"
        echo "ngrok start --all --config=ngrok.yml"
        echo ""
        echo "Teile die Ngrok Frontend URL zum Testen!"
        ;;
    
    3)
        echo -e "\n${GREEN}Manual Deploy Guide${NC}"
        echo "Backend:"
        echo "1. Deploy Docker Container auf beliebigem Cloud Provider"
        echo "2. Setup PostgreSQL & Redis"
        echo "3. Environment Variables setzen"
        echo ""
        echo "Frontend:"
        echo "1. npm run build"
        echo "2. Upload build/ Ordner zu Static Host"
        echo "3. CORS in Backend konfigurieren"
        ;;
esac

echo -e "\n${YELLOW}Wichtige Test-Schritte nach Deployment:${NC}"
echo "1. Erstelle ein Meeting auf der Hauptseite"
echo "2. Kopiere den Meeting-Link"
echo "3. Öffne den Link in einem anderen Browser/Gerät"
echo "4. Trete mit verschiedenen Namen bei"
echo "5. Teste Video, Audio und Screensharing"

echo -e "\n${GREEN}✅ Viel Erfolg beim Testing!${NC}" 