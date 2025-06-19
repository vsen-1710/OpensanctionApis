import redis
import json
import hashlib
import logging
from config import Config

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = None
        self.connect()
    
    def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def generate_cache_key(self, entity_name):
        """Generate a consistent cache key for an entity"""
        return f"entity_check:{hashlib.md5(entity_name.lower().encode()).hexdigest()}"
    
    def get(self, entity_name):
        """Retrieve entity data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self.generate_cache_key(entity_name)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for entity: {entity_name}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        
        return None
    
    def set(self, entity_name, data):
        """Store entity data in Redis cache with expiry"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self.generate_cache_key(entity_name)
            self.redis_client.setex(
                cache_key,
                Config.CACHE_EXPIRY_SECONDS,
                json.dumps(data)
            )
            logger.info(f"Data cached for entity: {entity_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def is_connected(self):
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def flush_cache(self):
        """Clear all cached data"""
        if not self.redis_client:
            return False
        
        try:
            # Only flush keys with our prefix
            keys = self.redis_client.keys("entity_check:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Flushed {len(keys)} cached entities")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False 