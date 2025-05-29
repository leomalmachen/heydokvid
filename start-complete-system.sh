#!/bin/bash

# Heydok Video - Complete System Startup Script
# This script starts the complete video meeting system with LiveKit

set -e  # Exit on any error

echo "🚀 Starting Heydok Video Complete System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f env.development ]; then
        print_status "Copying development environment configuration..."
        cp env.development .env
    elif [ -f env.example ]; then
        print_status "Copying example environment configuration..."
        cp env.example .env
        print_warning "Please edit .env file with your configuration before running in production!"
    else
        print_error "No environment configuration found. Please create .env file."
        exit 1
    fi
fi

# Start the complete system with docker-compose
print_status "Starting complete system with Docker Compose..."

# Use development compose file if it exists, otherwise use default
if [ -f docker-compose.dev.yml ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

print_status "Using compose file: $COMPOSE_FILE"

# Start services
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service status..."

# Check LiveKit
if docker-compose -f $COMPOSE_FILE ps livekit | grep -q "Up"; then
    print_success "✅ LiveKit is running"
else
    print_error "❌ LiveKit failed to start"
fi

# Check Backend
if docker-compose -f $COMPOSE_FILE ps backend | grep -q "Up"; then
    print_success "✅ Backend is running"
else
    print_error "❌ Backend failed to start"
fi

# Check Frontend (if exists)
if docker-compose -f $COMPOSE_FILE ps frontend 2>/dev/null | grep -q "Up"; then
    print_success "✅ Frontend is running"
else
    print_warning "⚠️  Frontend service not found or not running"
fi

# Show service URLs
echo ""
print_success "🎉 System is ready!"
echo ""
echo "📋 Service URLs:"
echo "   🎥 LiveKit Server:    ws://localhost:7880"
echo "   🔧 LiveKit Dashboard: http://localhost:7880"
echo "   🚀 Backend API:       http://localhost:8002"
echo "   📖 API Documentation: http://localhost:8002/api/docs"
echo "   🌐 Frontend:          http://localhost:3000 (if running)"
echo ""
echo "📝 Logs:"
echo "   View all logs:        docker-compose -f $COMPOSE_FILE logs -f"
echo "   View backend logs:    docker-compose -f $COMPOSE_FILE logs -f backend"
echo "   View livekit logs:    docker-compose -f $COMPOSE_FILE logs -f livekit"
echo ""
echo "🛑 To stop the system:"
echo "   docker-compose -f $COMPOSE_FILE down"
echo ""

# Show quick test
echo "🧪 Quick Test:"
echo "   Create meeting:       curl -X POST http://localhost:8002/api/v1/meetings/create"
echo ""

print_success "System startup complete! 🚀" 