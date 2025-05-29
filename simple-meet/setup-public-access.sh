#!/bin/bash

echo "🌐 Setting up public access for Simple Meet..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Installing..."
    
    # Detect OS and install ngrok
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ngrok/ngrok/ngrok
        else
            echo "Please install Homebrew first or download ngrok from https://ngrok.com/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt update && sudo apt install ngrok
    else
        echo "Please download ngrok from https://ngrok.com/download"
        exit 1
    fi
fi

# Create ngrok configuration
cat > ngrok-config.yml << EOF
version: "2"
authtoken: \${NGROK_AUTH_TOKEN}
tunnels:
  backend:
    addr: 5001
    proto: http
    hostname: \${NGROK_BACKEND_DOMAIN}
  frontend:
    addr: 3000
    proto: http
    hostname: \${NGROK_FRONTEND_DOMAIN}
EOF

echo "📝 ngrok configuration created."
echo ""
echo "To use ngrok for public access:"
echo ""
echo "1. Sign up for a free ngrok account at https://ngrok.com"
echo "2. Get your authtoken from https://dashboard.ngrok.com/auth"
echo "3. Run: ngrok authtoken YOUR_AUTH_TOKEN"
echo "4. Start ngrok with: ngrok start --all --config ngrok-config.yml"
echo ""
echo "For a simpler setup with random URLs:"
echo "Run in separate terminals:"
echo "  Terminal 1: ngrok http 5001"
echo "  Terminal 2: ngrok http 3000"
echo ""
echo "Then update the frontend to use the ngrok backend URL." 