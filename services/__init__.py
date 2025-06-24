# Services package 

# Authentication service for API key validation
from flask import request, jsonify
from functools import wraps
from config import Config
import logging

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate the provided API key against configured keys"""
        if not Config.REQUIRE_API_KEY:
            return True
        
        if not api_key:
            return False
        
        # Clean and validate the API key
        api_key = api_key.strip()
        valid_keys = [key.strip() for key in Config.API_KEYS if key.strip()]
        
        return api_key in valid_keys
    
    @staticmethod
    def get_api_key_from_request() -> str:
        """Extract API key from request headers or query parameters"""
        # Try header first
        api_key = request.headers.get(Config.API_KEY_HEADER)
        
        # Fallback to query parameter
        if not api_key:
            api_key = request.args.get('api_key')
        
        # Fallback to Authorization header (Bearer token format)
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        return api_key or ''

def require_api_key(f):
    """Decorator to require API key authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_API_KEY:
            return f(*args, **kwargs)
        
        api_key = AuthService.get_api_key_from_request()
        
        if not AuthService.validate_api_key(api_key):
            logger.warning(f"Invalid API key attempt: {api_key[:10]}..." if api_key else "No API key provided")
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': f'Please provide a valid API key in the {Config.API_KEY_HEADER} header',
                'api_version': '2.0.0'
            }), 401
        
        logger.info(f"Valid API key used: {api_key[:10]}...")
        return f(*args, **kwargs)
    
    return decorated_function 