from flask import Flask, jsonify
import logging
from routes.api_routes import api_bp
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v2')
    
    # Root endpoint with API documentation
    @app.route('/')
    def root():
        return jsonify({
            'api_name': 'OpenSanctions Enhanced API',
            'version': '2.0.0',
            'description': 'Enhanced entity checking with intelligent web search',
            'endpoints': {
                'check_entity': {
                    'method': 'POST',
                    'url': '/api/v2/check',
                    'description': 'Check entity by name with OpenSanctions and web search',
                    'body_example': {
                        'name': 'John Smith'
                    }
                },
                'check_entity_by_id': {
                    'method': 'GET',
                    'url': '/api/v2/check/{entity_id}',
                    'description': 'Check entity by OpenSanctions entity ID',
                    'example': '/api/v2/check/os-123456'
                },
                'health': {
                    'method': 'GET',
                    'url': '/api/v2/health',
                    'description': 'Health check endpoint'
                }
            },
            'features': [
                'OpenSanctions database integration',
                'Intelligent web search with trusted sources',
                'Entity ID-based checking',
                'Comprehensive result analysis',
                'Rate limiting and error handling'
            ]
        })
    
    return app

# Create the Flask app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    logger.info("OpenSanctions Enhanced API v2.0.0 created successfully")
    logger.info("Starting OpenSanctions Enhanced API server v2.0.0...")
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_ENV == 'development'
    ) 