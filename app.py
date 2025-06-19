from flask import Flask, jsonify
import logging
from config import Config
from routes.api_routes import api_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for production-ready OpenSanctions API"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'available_endpoints': [
                'POST /check - Enhanced entity checking with intelligent web search',
                'GET /health - Service health status',
                'POST /clear-cache - Clear cached data (requires auth)'
            ],
            'api_version': '2.0.0'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'api_version': '2.0.0'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request - Invalid JSON or request format',
            'api_version': '2.0.0'
        }), 400
    
    # Root endpoint with API documentation
    @app.route('/')
    def root():
        return jsonify({
            'service': 'OpenSanctions Enhanced API',
            'version': '2.0.0',
            'description': 'Simplified sanctions and compliance checking with clean, focused results',
            'endpoints': {
                'POST /check': {
                    'description': 'Check entities against OpenSanctions database with clean, simplified output',
                    'features': [
                        'OpenSanctions database search',
                        'Support for people, companies, and organizations',
                        'Clean, focused output format',
                        'Detailed entity information',
                        'Source attribution and descriptions'
                    ]
                },
                'GET /health': {
                    'description': 'Check API and service health status',
                    'returns': 'Service status and configuration'
                },
                'POST /clear-cache': {
                    'description': 'Clear cached data (admin only)',
                    'requires': 'Authorization Bearer token'
                },
                'GET|POST /test-opensanctions': {
                    'description': 'Test OpenSanctions API connection and configuration (debugging)',
                    'parameters': 'entity (optional) - entity name to test search with',
                    'example': '/test-opensanctions?entity=Vladimir Putin'
                }
            },
            'supported_entity_types': [
                'People/Individuals',
                'Companies/Corporations', 
                'Organizations',
                'Vessels',
                'Aircraft',
                'Other legal entities'
            ],
            'supported_input_formats': {
                'single_person': {
                    'name': 'John Doe'
                },
                'single_company': {
                    'company': 'Acme Corporation'
                },
                'single_organization': {
                    'organization': 'ABC Foundation'
                },
                'generic_entity': {
                    'entity': 'Entity Name'
                },
                'enhanced_entity': {
                    'entity': {
                        'name': 'Entity Name',
                        'type': 'person|company|organization'
                    }
                },
                'multiple_entities': [
                    {'name': 'Person Name'},
                    {'company': 'Company Name'},
                    {'organization': 'Org Name'}
                ],
                'batch_format': {
                    'entities': [
                        {'name': 'Entity 1'},
                        {'company': 'Entity 2'}
                    ]
                },
                'legacy_format': {
                    'queries': ['Entity Name 1', 'Entity Name 2']
                }
            },
            'response_format': {
                'found': 'boolean - whether entity was found',
                'summary': 'string - clean summary of findings',
                'details': 'object - entity details if found',
                'source_info': 'object - source information and descriptions'
            },
            'example_response': {
                'success': True,
                'entity': {'name': 'Cele, Faith'},
                'result': {
                    'entity_name': 'Cele, Faith',
                    'found': True,
                    'summary': 'Cele, Faith\nCrime · Wanted\nCele, Faith is a person of interest. They have been found on international compliance databases.',
                    'details': {
                        'type': 'Person',
                        'name': 'Cele, Faith',
                        'category': 'Crime · Wanted',
                        'country': 'South Africa',
                        'source_link': 'www.saps.gov.za'
                    },
                    'source_info': {
                        'datasets': ['za_wanted'],
                        'descriptions': [
                            {
                                'text': 'Wanted - Shoplifting',
                                'source': 'South Africa Wanted Persons',
                                'date': '2024-08-08'
                            }
                        ]
                    }
                }
            },
            'documentation': 'Simplified API with clean, focused compliance results'
        })
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        """Detailed API information"""
        return jsonify({
            'api_version': '2.0.0',
            'service_name': 'OpenSanctions Enhanced API',
            'capabilities': {
                'database_search': 'OpenSanctions comprehensive database',
                'intelligent_web_search': 'AI-powered web search with relevance ranking',
                'risk_assessment': 'Multi-factor risk scoring system',
                'trusted_sources': 'Curated list of reliable news and government sources',
                'caching': 'Redis-based result caching for performance'
            },
            'data_sources': [
                'OpenSanctions.org - Global sanctions and compliance database',
                'Trusted news sources (BBC, Reuters, AP News, etc.)',
                'Government websites (Treasury.gov, SEC.gov, etc.)',
                'Financial industry publications'
            ],
            'compliance_features': [
                'AML (Anti-Money Laundering) checks',
                'Sanctions screening',
                'PEP (Politically Exposed Persons) identification',
                'Wanted persons database search',
                'Regulatory enforcement tracking'
            ]
        })
    
    logger.info("OpenSanctions Enhanced API v2.0.0 created successfully")
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    logger.info("Starting OpenSanctions Enhanced API server v2.0.0...")
    app.run(
        host='0.0.0.0',
        port=int(Config.FLASK_PORT if hasattr(Config, 'FLASK_PORT') else 5000),
        debug=Config.FLASK_ENV == 'development'
    ) 