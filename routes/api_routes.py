from flask import Blueprint, request, jsonify
import logging
from typing import Dict, List, Any, Optional
from services.entity_service import EntityService

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)

# Initialize services
entity_service = EntityService()

@api_bp.route('/check', methods=['POST'])
def check_entities():
    """Enhanced entity checking with intelligent web search"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400
        
        # Check if this is a direct entity ID check
        if 'id' in data and isinstance(data['id'], str):
            # Direct entity ID check
            entity_id = data['id'].strip()
            if not entity_id:
                return jsonify({'error': 'Entity ID cannot be empty'}), 400
            
            result = entity_service.process_entity_by_id(entity_id)
            return jsonify({
                'success': True,
                'entity_id': entity_id,
                'result': result,
                'api_version': '2.0.0'
            })
        
        # Check if this is a list of entity records
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'id' in data[0]:
            # List of entity records
            entity_ids = []
            for record in data:
                if isinstance(record, dict) and 'id' in record:
                    entity_ids.append(record['id'])
            
            if not entity_ids:
                return jsonify({'error': 'No valid entity IDs found in request'}), 400
            
            if len(entity_ids) > 50:  # Limit to prevent abuse
                return jsonify({'error': 'Maximum 50 entities allowed per request'}), 400
            
            # Process entity IDs
            results = []
            for entity_id in entity_ids:
                result = entity_service.process_entity_by_id(entity_id)
                results.append({
                    'entity_id': entity_id,
                    'result': result
                })
            
            return jsonify({
                'success': True,
                'total_entities': len(entity_ids),
                'results': results,
                'api_version': '2.0.0'
            })
        
        # Parse entities from different input formats
        entities = _parse_entities(data)
        
        if not entities:
            return jsonify({'error': 'No valid entities found in request'}), 400
        
        if len(entities) > 50:  # Limit to prevent abuse
            return jsonify({'error': 'Maximum 50 entities allowed per request'}), 400
        
        # Process entities
        results = entity_service.process_multiple_entities(entities)
        
        # Format response based on input type
        if len(entities) == 1 and ('name' in data or 'entity' in data):
            # Single entity response format
            result = results[0] if results else None
            entity_field = data.get('name', data.get('entity', entities[0]))
            return jsonify({
                'success': True,
                'entity': {'name': entity_field},
                'result': result,
                'api_version': '2.0.0'
            })
        
        # Multiple entities response format
        return jsonify({
            'success': True,
            'total_entities': len(entities),
            'results': results,
            'api_version': '2.0.0'
        })
        
    except Exception as e:
        logger.error(f"Error in /check endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'api_version': '2.0.0'
        }), 500

@api_bp.route('/check/<entity_id>', methods=['GET'])
def check_entity_by_id(entity_id: str):
    """Check entity by OpenSanctions entity ID"""
    try:
        if not entity_id or not entity_id.strip():
            return jsonify({'error': 'Entity ID is required'}), 400
        
        # Process entity by ID
        result = entity_service.process_entity_by_id(entity_id.strip())
        
        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'result': result,
            'api_version': '2.0.0'
        })
        
    except Exception as e:
        logger.error(f"Error in /check/{entity_id} endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'api_version': '2.0.0'
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        health_status = entity_service.get_health_status()
        
        status = {
            'status': 'healthy',
            'services': {
                'cache': 'connected' if health_status['cache_connected'] else 'disconnected',
                'opensanctions': 'configured' if health_status['opensanctions_configured'] else 'not_configured',
                'search': 'configured' if health_status['search_configured'] else 'not_configured'
            },
            'search_providers': health_status['search_providers'],
            'api_version': '2.0.0'
        }
        
        # Return 503 if critical services are down
        if not health_status['opensanctions_configured']:
            status['status'] = 'degraded'
            return jsonify(status), 503
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'api_version': '2.0.0'
        }), 500

@api_bp.route('/check/entity-id', methods=['POST'])
def check_entity_by_id_json():
    """Check entity by ID from JSON input"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400
        
        # Handle single entity ID
        if 'id' in data and isinstance(data['id'], str):
            entity_id = data['id'].strip()
            if not entity_id:
                return jsonify({'error': 'Entity ID cannot be empty'}), 400
            
            result = entity_service.process_entity_by_id(entity_id)
            return jsonify({
                'success': True,
                'entity_id': entity_id,
                'result': result,
                'api_version': '2.0.0'
            })
        
        # Handle list of entity IDs
        if 'ids' in data and isinstance(data['ids'], list):
            entity_ids = [str(id).strip() for id in data['ids'] if str(id).strip()]
            
            if not entity_ids:
                return jsonify({'error': 'No valid entity IDs found in request'}), 400
            
            if len(entity_ids) > 50:  # Limit to prevent abuse
                return jsonify({'error': 'Maximum 50 entities allowed per request'}), 400
            
            # Process entity IDs
            results = []
            for entity_id in entity_ids:
                result = entity_service.process_entity_by_id(entity_id)
                results.append({
                    'entity_id': entity_id,
                    'result': result
                })
            
            return jsonify({
                'success': True,
                'total_entities': len(entity_ids),
                'results': results,
                'api_version': '2.0.0'
            })
        
        # Handle list of entity records (like your JSON format)
        if isinstance(data, list) and len(data) > 0:
            entity_ids = []
            for record in data:
                if isinstance(record, dict) and 'id' in record:
                    entity_ids.append(record['id'])
            
            if not entity_ids:
                return jsonify({'error': 'No valid entity IDs found in request'}), 400
            
            if len(entity_ids) > 50:  # Limit to prevent abuse
                return jsonify({'error': 'Maximum 50 entities allowed per request'}), 400
            
            # Process entity IDs
            results = []
            for entity_id in entity_ids:
                result = entity_service.process_entity_by_id(entity_id)
                results.append({
                    'entity_id': entity_id,
                    'result': result
                })
            
            return jsonify({
                'success': True,
                'total_entities': len(entity_ids),
                'results': results,
                'api_version': '2.0.0'
            })
        
        return jsonify({'error': 'Invalid request format. Expected "id", "ids", or list of entity records'}), 400
        
    except Exception as e:
        logger.error(f"Error in /check/entity-id endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'api_version': '2.0.0'
        }), 500

def _parse_entities(data: Dict) -> List[str]:
    """Parse entities from various input formats supporting different entity types"""
    entities = []
    
    try:
        # Format 1: Single entity with name field
        if 'name' in data and isinstance(data['name'], str):
            entity_name = data['name'].strip()
            if entity_name:
                entities.append(entity_name)
        
        # Format 2: New format with entity field
        elif 'entity' in data and isinstance(data['entity'], str):
            entity_name = data['entity'].strip()
            if entity_name:
                entities.append(entity_name)
        
        # Format 3: Company/Organization specific fields
        elif 'company' in data and isinstance(data['company'], str):
            entity_name = data['company'].strip()
            if entity_name:
                entities.append(entity_name)
        
        elif 'organization' in data and isinstance(data['organization'], str):
            entity_name = data['organization'].strip()
            if entity_name:
                entities.append(entity_name)
        
        # Format 4: Enhanced entity object with type information
        elif 'entity' in data and isinstance(data['entity'], dict):
            entity_obj = data['entity']
            entity_name = entity_obj.get('name', '').strip()
            if entity_name:
                entities.append(entity_name)
        
        # Format 5: List of entities (supports mixed types)
        elif isinstance(data, list):
            for item in data:
                entity_name = None
                
                if isinstance(item, dict):
                    # Try different name fields
                    for field in ['name', 'entity', 'company', 'organization']:
                        if field in item:
                            entity_name = item[field].strip()
                            break
                elif isinstance(item, str):
                    entity_name = item.strip()
                
                if entity_name:
                    entities.append(entity_name)
        
        # Format 6: Queries array (legacy support)
        elif 'queries' in data and isinstance(data['queries'], list):
            for query in data['queries']:
                entity_name = None
                
                if isinstance(query, str):
                    entity_name = query.strip()
                elif isinstance(query, dict):
                    for field in ['name', 'entity', 'company', 'organization']:
                        if field in query:
                            entity_name = query[field].strip()
                            break
                
                if entity_name:
                    entities.append(entity_name)
        
        # Format 7: Batch format with entities array
        elif 'entities' in data and isinstance(data['entities'], list):
            for entity_obj in data['entities']:
                entity_name = None
                
                if isinstance(entity_obj, dict):
                    for field in ['name', 'entity', 'company', 'organization']:
                        if entity_obj[field]:
                            entity_name = entity_obj[field].strip()
                            break
                elif isinstance(entity_obj, str):
                    entity_name = entity_obj.strip()
                
                if entity_name:
                    entities.append(entity_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities
        
    except Exception as e:
        logger.error(f"Error parsing entities: {e}")
        return []

# Error handlers for the blueprint
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'api_version': '2.0.0'
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'api_version': '2.0.0'
    }), 405 