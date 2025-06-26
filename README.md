# OpenSanctions API

A powerful Flask API that provides comprehensive entity compliance checking by combining OpenSanctions data with intelligent web search results. Features Redis caching, API key authentication, and advanced risk assessment.

## 🚀 Features

- **🔍 Entity Checking**: Check entities against OpenSanctions database using entity IDs or names
- **🌐 Web Search Integration**: Intelligent web search with trusted domain filtering
- **⚡ Redis Caching**: Fast response times with configurable cache expiry
- **🔐 API Key Authentication**: Secure access control with multiple API key support
- **📊 Risk Assessment**: Automated risk scoring and analysis
- **🔄 Multiple Input Formats**: Support for single entities, entity lists, and complex entity data
- **🐳 Docker Support**: Full Docker and Docker Compose deployment
- **📈 Health Monitoring**: Built-in health checks and status endpoints

## 🏗️ Architecture

```
opensanctionapi/
├── app.py                 # Main Flask application with Swagger setup
├── config.py             # Configuration management and validation
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker Compose setup
├── Dockerfile           # Docker image definition
├── nginx.conf/          # Nginx configuration
├── services/            # Business logic services
│   ├── __init__.py
│   ├── cache_service.py        # Redis cache operations
│   ├── opensanctions_service.py # OpenSanctions API client
│   ├── search_service.py       # Web search API client
│   └── entity_service.py       # Main entity processing logic
└── routes/              # API routes
    ├── __init__.py
    └── api_routes.py    # All API endpoints with authentication
```

## 🛠️ Quick Setup

### Prerequisites

- Python 3.8+
- Redis server
- OpenSanctions API key
- Serper API key (for web search)

### 1. Clone and Install

```bash
git clone <repository-url>
cd opensanctionapi
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your configuration:

```env
# Required: OpenSanctions API Key
OPENSANCTIONS_API_KEY=your_actual_opensanctions_api_key

# Required: Web Search API Key
SERPER_API_KEY=your_actual_serper_api_key

# API Authentication (comma-separated list)
API_KEYS=your_api_key_1,your_api_key_2,demo_key_789012

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_EXPIRY_SECONDS=3600

# Flask Configuration
FLASK_ENV=development
FLASK_PORT=5000
SECRET_KEY=your-secret-key-here

# Admin Configuration
ADMIN_TOKEN=your-admin-token
```

### 3. Choose Your Setup Method

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

## 📚 API Documentation

### Authentication

All endpoints require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key" http://localhost:5000/api/v2/health
```

### POST /api/v2/check

Check entities against sanctions databases with web search integration.

**Request Formats:**

1. **Single Entity ID:**
```json
{
  "id": "Q123456"
}
```

2. **Entity Name:**
```json
{
  "name": "John Doe"
}
```

3. **Multiple Entities:**
```json
[
  {"id": "Q123"},
  {"id": "Q456"}
]
```

4. **Complex Entity:**
```json
{
  "name": "John Doe",
  "alias": "Johnny",
  "country": "US",
  "gender": "male",
  "dob": "1990-01-01"
}
```

**Response:**
```json
{
  "success": true,
  "entity": {
    "name": "John Doe"
  },
  "result": {
    "found": true,
    "results": [
      {
        "opensanctions": {
          "name": "John Doe",
          "type": "Person",
          "relevance": "high"
        }
      }
    ],
    "status": "completed",
    "summary": "Found in OpenSanctions (2 records)",
    "total_results": 1
  },
  "api_version": "2.0.0"
}
```

### GET /api/v2/check/{entity_id}

Check a specific entity by ID.

```bash
curl -H "X-API-Key: your_api_key" http://localhost:5000/api/v2/check/Q123456
```

### GET /api/v2/health

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
  "timestamp": 1703123456
}
```

### GET /api/v2/cache/status

Check cache status and statistics.

**Response:**
```json
{
  "cache_enabled": true,
  "redis_connected": true,
  "total_keys": 150,
  "memory_usage": "2.5MB"
}
```

### POST /api/v2/cache/clear

Clear all cached data.

**Response:**
```json
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

### POST /api/v2/cache/clear/{entity_name}

Clear cache for a specific entity.

```bash
curl -X POST -H "X-API-Key: your_api_key" http://localhost:5000/api/v2/cache/clear/John%20Doe
```

### GET /api/v2/auth/validate

Validate your API key.

**Response:**
```json
{
  "valid": true,
  "message": "API key is valid"
}
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENSANCTIONS_API_KEY` | OpenSanctions API key | Required |
| `SERPER_API_KEY` | Serper web search API key | Required |
| `API_KEYS` | Comma-separated list of valid API keys | Required |
| `REDIS_HOST` | Redis server host | localhost |
| `REDIS_PORT` | Redis server port | 6379 |
| `CACHE_EXPIRY_SECONDS` | Cache expiration time | 3600 |
| `MAX_ENTITIES_PER_REQUEST` | Maximum entities per request | 50 |
| `REQUEST_TIMEOUT` | API request timeout | 10 |
| `FLASK_PORT` | Flask application port | 5000 |

### Trusted Domains

Web search is restricted to these trusted domains:
- **News**: bbc.com, reuters.com, apnews.com, cnn.com, theguardian.com, wsj.com, ft.com, bloomberg.com, hindustantimes.com, forbes.com
- **Government**: treasury.gov, fincen.gov, sec.gov, fbi.gov, justice.gov, state.gov, europa.eu
- **Compliance**: opensanctions.org, sanctionslist.eu, ofac.treasury.gov, un.org
- **Financial**: swift.com, fatf-gafi.org, wolfsberg-principles.com

## 🧪 Testing

Test the API endpoints:

```bash
# Health check
curl http://localhost:5000/api/v2/health

# Entity check (requires API key)
curl -X POST http://localhost:5000/api/v2/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"name": "John Doe"}'

# Cache status
curl -H "X-API-Key: your_api_key" http://localhost:5000/api/v2/cache/status

# Clear cache
curl -X POST -H "X-API-Key: your_api_key" http://localhost:5000/api/v2/cache/clear
```

## 🐳 Docker Commands

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

# Access Redis CLI
docker exec -it opensanctionapi_redis_1 redis-cli
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

## 📊 Risk Assessment

**Risk Levels:**
- `low`: Risk score 0 (no findings)
- `medium`: Risk score 1-2 (some web mentions)
- `high`: Risk score 3+ (sanctions database match or multiple risk indicators)

**Risk Factors:**
- Found in sanctions database (+3 points)
- Web mentions of sanctions/compliance keywords (+1 point each)

## 🚀 Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. Configure reverse proxy (Nginx)
4. Enable HTTPS
5. Set up monitoring and logging
6. Change default admin token

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
- Check `/health` endpoint for configuration status
- Review logs for authentication errors

**Docker Issues:**
```bash
# Check container logs
docker-compose logs opensanctions-api
docker-compose logs redis

# Restart services
docker-compose restart
```

**Common Issues:**
- Ensure all required environment variables are set
- Check Redis connectivity
- Verify API keys are valid
- Monitor request timeouts

## 📝 License

This project is licensed under the MIT License. 