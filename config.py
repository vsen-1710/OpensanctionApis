import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # OpenSanctions API
    OPENSANCTIONS_API_KEY = os.getenv('OPENSANCTIONS_API_KEY')
    
    # Web Search API (Serper)
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')
    SERPER_API_URL = os.getenv('SERPER_API_URL', 'https://google.serper.dev/search')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    CACHE_EXPIRY_SECONDS = int(os.getenv('CACHE_EXPIRY_SECONDS', 3600))
    
    # Admin Configuration
    ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'admin-token-change-in-production')
    
    # Rate Limiting
    MAX_ENTITIES_PER_REQUEST = int(os.getenv('MAX_ENTITIES_PER_REQUEST', 50))
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 100))
    
    # Trusted domains for web search (curated list of reliable sources)
    TRUSTED_DOMAINS = [
        # News Sources
        'bbc.com',
        'reuters.com',
        'apnews.com',
        'cnn.com',
        'theguardian.com',
        'wsj.com',
        'ft.com',
        'bloomberg.com',
        'hindustantimes.com',
        'forbes.com',
        
        # Government Sources
        'treasury.gov',
        'fincen.gov',
        'sec.gov',
        'fbi.gov',
        'justice.gov',
        'state.gov',
        'europa.eu',
        
        # Compliance and Legal
        'opensanctions.org',
        'sanctionslist.eu',
        'ofac.treasury.gov',
        'un.org',
        
        # Financial Industry
        'swift.com',
        'fatf-gafi.org',
        'wolfsberg-principles.com'
    ]
    
    # Performance Configuration - Optimized for faster response times
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))  # Reduced from 30 to 10
    SEARCH_RESULTS_LIMIT = int(os.getenv('SEARCH_RESULTS_LIMIT', 5))  # Reduced from 10 to 5
    
    # New optimization settings
    OPENSANCTIONS_TIMEOUT = int(os.getenv('OPENSANCTIONS_TIMEOUT', 10))  # 10 second timeout
    WEB_SEARCH_TIMEOUT = int(os.getenv('WEB_SEARCH_TIMEOUT', 8))  # 8 second timeout
    PARALLEL_PROCESSING_TIMEOUT = int(os.getenv('PARALLEL_PROCESSING_TIMEOUT', 15))  # 15 second timeout for parallel tasks
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        errors = []
        
        if not cls.OPENSANCTIONS_API_KEY:
            errors.append("OPENSANCTIONS_API_KEY is required")
        
        if not cls.SERPER_API_KEY:
            errors.append("SERPER_API_KEY is required for web search functionality")
        
        if cls.FLASK_ENV == 'production' and cls.ADMIN_TOKEN == 'admin-token-change-in-production':
            errors.append("ADMIN_TOKEN must be changed in production")
        
        return errors 