#!/bin/bash

echo "🚀 OpenSanctions API Setup Script"
echo "=================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
docker_running() {
    docker info >/dev/null 2>&1
}

echo "📋 Checking prerequisites..."

# Check Python
if command_exists python3; then
    echo "✅ Python3 is installed"
    python3 --version
else
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check pip
if command_exists pip3; then
    echo "✅ pip3 is installed"
else
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Check Docker
if command_exists docker; then
    echo "✅ Docker is installed"
    if docker_running; then
        echo "✅ Docker is running"
    else
        echo "⚠️  Docker is installed but not running. Please start Docker."
    fi
else
    echo "⚠️  Docker is not installed. You can still run the app without Docker, but you'll need to install Redis manually."
fi

# Check docker-compose
if command_exists docker-compose; then
    echo "✅ Docker Compose is installed"
elif command_exists docker && docker compose version >/dev/null 2>&1; then
    echo "✅ Docker Compose (v2) is available"
else
    echo "⚠️  Docker Compose is not available."
fi

echo ""
echo "🔧 Setting up the application..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "⚠️  Please edit .env file and add your API keys!"
    echo "   - Get OpenSanctions API key from: https://opensanctions.org/"
    echo "   - Get Serper API key from: https://serper.dev/"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Docker Setup Options:"
echo "========================"
echo "1. Run with Docker Compose (recommended)"
echo "2. Run Redis in Docker, app locally"
echo "3. Run everything locally (requires local Redis)"
echo ""

read -p "Choose an option (1-3): " choice

case $choice in
    1)
        echo "🐳 Setting up with Docker Compose..."
        if command_exists docker-compose; then
            docker-compose up -d
        elif command_exists docker && docker compose version >/dev/null 2>&1; then
            docker compose up -d
        else
            echo "❌ Docker Compose not available. Please install Docker Compose."
            exit 1
        fi
        echo "✅ Application should be running at http://localhost:5000"
        ;;
    2)
        echo "🐳 Starting Redis in Docker..."
        docker run -d -p 6379:6379 --name opensanctions_redis redis:7-alpine
        echo "🚀 Starting Flask app locally..."
        echo "Make sure your .env file has REDIS_HOST=localhost"
        python3 app.py &
        ;;
    3)
        echo "🔧 Local setup selected."
        echo "Please ensure Redis is running locally on port 6379"
        echo "To start Redis:"
        echo "  - Ubuntu/Debian: sudo systemctl start redis-server"
        echo "  - macOS: brew services start redis"
        echo "  - Manual: redis-server"
        echo ""
        read -p "Press Enter when Redis is running, then we'll start the app..."
        python3 app.py &
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🧪 Testing the API..."
sleep 3  # Give the app time to start

# Test the health endpoint
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ API is responding!"
    echo ""
    echo "🎉 Setup complete!"
    echo "==================="
    echo "📍 API URL: http://localhost:5000"
    echo "🏥 Health check: http://localhost:5000/health"
    echo "📊 Status: http://localhost:5000/status"
    echo ""
    echo "📖 To test the API:"
    echo "   python3 test_api.py"
    echo ""
    echo "📝 Don't forget to:"
    echo "   1. Edit .env file with your API keys"
    echo "   2. Check the README.md for full documentation"
else
    echo "❌ API is not responding. Please check the logs and try again."
fi 