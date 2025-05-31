#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
LIVEKIT_URL=wss://heydok-5pbd24sq.livekit.cloud
LIVEKIT_API_KEY=APIysK82G8HGmFr
LIVEKIT_API_SECRET=ytVhapnJwHIzfQzzqZL3sPbSJfelfdBcCtD2vCwm0bbA
EOL
    echo ".env file created!"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start the server
echo "Starting server..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 