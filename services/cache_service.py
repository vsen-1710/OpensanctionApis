import redis
import json
import hashlib
import logging
from config import Config
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = None
        self.cache_prefix = "opensanctions:"
        # Cache version - increment this when you change filtering logic
        self.cache_version = "v2"  # Updated cache version for new filtering logic
        self.default_ttl = 3600  # 1 hour
        
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.redis_client = None

    def _get_cache_key(self, entity_name: str) -> str:
        """Generate cache key with version for entity"""
        return f"{self.cache_prefix}{self.cache_version}:{entity_name.lower().strip()}"
    
    def get(self, entity_name):
        """Retrieve entity data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(entity_name)
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
            cache_key = self._get_cache_key(entity_name)
            self.redis_client.setex(
                cache_key,
                self.default_ttl,
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
        if not self.is_connected():
            return False
        
        try:
            # Only flush keys with our prefix
            keys = self.redis_client.keys(f"{self.cache_prefix}*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Flushed {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
    
    def clear_entity_cache(self, entity_name: str) -> bool:
        """Clear cache for a specific entity"""
        if not self.is_connected():
            return False
        
        try:
            cache_key = self._get_cache_key(entity_name)
            result = self.redis_client.delete(cache_key)
            logger.info(f"Cleared cache for entity: {entity_name}")
            return result > 0
        except Exception as e:
            logger.error(f"Error clearing cache for {entity_name}: {e}")
            return False
    
    def get_cache_info(self) -> Dict:
        """Get cache statistics and information"""
        if not self.is_connected():
            return {"connected": False, "cache_version": self.cache_version}
        
        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}*")
            return {
                "connected": True,
                "cache_version": self.cache_version,
                "total_cached_entities": len(keys),
                "cache_ttl": self.default_ttl
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"connected": False, "error": str(e)} 