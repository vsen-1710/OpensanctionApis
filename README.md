# OpenSanctions API

A modular Flask API that combines OpenSanctions data with web search results to provide comprehensive entity compliance checking with Redis caching.

## 🚀 Features

- **POST /check**: Check multiple entities for sanctions and compliance issues
- **GET /health**: Health monitoring endpoint
- **GET /status**: Detailed API status information
- **POST /cache/clear**: Clear all cached data
- **Redis Caching**: Automatic caching with configurable expiry
- **Multiple Data Sources**: Combines OpenSanctions API with web search
- **Domain Restrictions**: Web search limited to trusted news and government domains
- **Risk Assessment**: Automated risk scoring based on findings
- **Modular Architecture**: Separate services and routes for maintainability
- **Docker Support**: Full Docker and Docker Compose support

## 🏗️ Architecture

```
opensanctionapi/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker Compose setup
├── Dockerfile           # Docker image definition
├── setup.sh            # Automated setup script
├── test_api.py         # API testing script
├── env.example         # Environment variables example
├── services/           # Business logic services
│   ├── __init__.py
│   ├── cache_service.py        # Redis cache operations
│   ├── opensanctions_service.py # OpenSanctions API client
│   ├── search_service.py       # Web search API client
│   └── entity_service.py       # Main entity processing logic
└── routes/             # API routes
    ├── __init__.py
    └── api_routes.py   # All API endpoints
```

## 🛠️ Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Check prerequisites
- Install dependencies
- Create environment file
- Offer Docker or local setup options
- Test the API

### Option 2: Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Setup Environment

```bash
cp env.example .env
# Edit .env with your API keys
```

#### 3. Choose Your Setup Method

**Docker Compose (Recommended):**
```bash
docker-compose up -d
```

**Redis in Docker, App Locally:**
```bash
docker run -d -p 6379:6379 --name opensanctions_redis redis:7-alpine
python app.py
```

**Everything Local:**
```bash
# Install and start Redis locally
sudo systemctl start redis-server  # Ubuntu/Debian
# OR
brew services start redis          # macOS

python app.py
```

## 📋 Environment Configuration

Copy `env.example` to `.env` and configure:

```env
# Required: OpenSanctions API Key
OPENSANCTIONS_API_KEY=your_actual_opensanctions_api_key

# Required: Web Search API Key
SERPER_API_KEY=your_actual_serper_api_key

# Redis Configuration (defaults work for Docker)
REDIS_HOST=localhost  # Use 'redis' for docker-compose
REDIS_PORT=6379
CACHE_EXPIRY_SECONDS=3600

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

## 📚 API Documentation

### POST /check

Check multiple entities for sanctions and compliance issues.

**Request:**
```json
{
  "queries": [
    "John Doe",
    "ACME Corporation",
    "Example LLC"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total_queries": 3,
  "results": [
    {
      "entity_name": "John Doe",
      "timestamp": 1703123456,
      "opensanctions": {
        "success": true,
        "data": {...},
        "total_results": 2
      },
      "web_search": {
        "success": true,
        "data": {...},
        "search_query": "John Doe sanctions OR compliance...",
        "provider": "serper"
      },
      "risk_assessment": "high",
      "risk_score": 4,
      "risk_factors": [
        "Found in sanctions database",
        "Web mention: sanctions"
      ]
    }
  ]
}
```

### GET /health

Quick health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "apis_configured": {
    "opensanctions": true,
    "search": true
  },
  "search_providers": ["serper"]
}
```

### GET /status

Detailed API status information.

**Response:**
```json
{
  "api_version": "1.0.0",
  "services": {
    "cache": {
      "connected": true,
      "type": "Redis"
    },
    "opensanctions": {
      "configured": true,
      "type": "OpenSanctions API"
    },
    "search": {
      "configured": true,
      "providers": ["serper"]
    }
  },
  "endpoints": [
    "POST /check - Check entities for sanctions",
    "GET /health - Health check",
    "POST /cache/clear - Clear cache",
    "GET /status - API status"
  ]
}
```

### POST /cache/clear

Clear all cached entity data.

**Response:**
```json
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_api.py
```

Or test individual endpoints:

```bash
# Health check
curl http://localhost:5000/health

# Entity check
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"queries": ["John Doe", "ACME Corp"]}'

# Clear cache
curl -X POST http://localhost:5000/cache/clear
```

## 🔧 Development

### Project Structure

- **`services/`**: Business logic separated by responsibility
  - `cache_service.py`: Redis operations
  - `opensanctions_service.py`: OpenSanctions API integration
  - `search_service.py`: Web search API integration
  - `entity_service.py`: Main entity processing coordinator

- **`routes/`**: API endpoints separated from business logic
  - `api_routes.py`: All Flask routes using Blueprint pattern

### Adding New Services

1. Create a new service class in `services/`
2. Import and integrate in `entity_service.py`
3. Add routes in `routes/api_routes.py` if needed

### Docker Commands

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

## 🔐 API Keys Setup

### OpenSanctions API
1. Visit [OpenSanctions](https://opensanctions.org/)
2. Sign up for API access
3. Add your API key to `.env` as `OPENSANCTIONS_API_KEY`

### Serper API (Web Search)
1. Visit [Serper.dev](https://serper.dev/)
2. Sign up and get your API key
3. Add your API key to `.env` as `SERPER_API_KEY`

## 🌐 Trusted Domains

Web search is restricted to these trusted domains:
- bbc.com, hindustantimes.com, opensanctions.org
- forbes.com, apnews.com, treasury.gov, fincen.gov
- reuters.com, cnn.com, theguardian.com, wsj.com
- sec.gov, ft.com

## 📊 Risk Assessment

**Risk Levels:**
- `low`: Risk score 0 (no findings)
- `medium`: Risk score 1-2 (some web mentions)
- `high`: Risk score 3+ (sanctions database match or multiple risk indicators)

**Risk Factors:**
- Found in sanctions database (+3 points)
- Web mentions of sanctions/compliance keywords (+1 point each)

## 🔒 Security Features

- Environment-based configuration
- Input validation and sanitization
- Request size limitations (max 50 entities)
- API timeouts (30 seconds)
- Domain-restricted web search
- Non-root Docker containers

## 🚀 Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (gunicorn recommended):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. Set up reverse proxy (nginx recommended)
4. Enable HTTPS
5. Configure monitoring and logging

## 🐛 Troubleshooting

**Redis Connection Issues:**
```bash
# Check Redis status
docker ps | grep redis
# OR
redis-cli ping
```

**API Key Issues:**
- Verify keys in `.env` file
- Check `/status` endpoint for configuration status
- Review logs for authentication errors

**Docker Issues:**
```bash
# Check container logs
docker-compose logs app
docker-compose logs redis

# Restart services
docker-compose restart
```

## 📝 License

This project is licensed under the MIT License. 