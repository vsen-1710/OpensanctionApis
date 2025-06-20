import requests
import logging
import re
from config import Config

logger = logging.getLogger(__name__)

class OpenSanctionsService:
    def __init__(self):
        self.api_key = Config.OPENSANCTIONS_API_KEY
        self.base_url = 'https://api.opensanctions.org'
        # Use proper collections as recommended by OpenSanctions API docs
        self.collections = ['default', 'sanctions', 'crime']
    
    def search_entity(self, entity_name):
        """Call OpenSanctions API to get sanctions data"""
        try:
            if not self.api_key:
                logger.warning("OpenSanctions API key not configured")
                return {
                    'success': False,
                    'error': 'OpenSanctions API key not configured',
                    'data': None,
                    'total_results': 0
                }
            
            # Check if entity_name looks like an entity ID (WikiData ID format: Q followed by digits)
            if self._is_entity_id(entity_name):
                logger.info(f"Detected entity ID format for: {entity_name}, attempting direct entity lookup")
                direct_result = self._get_entity_by_id(entity_name)
                if direct_result.get('success') and direct_result.get('total_results', 0) > 0:
                    return direct_result
                # If direct lookup fails, continue with normal search
                logger.info(f"Direct entity lookup failed for {entity_name}, falling back to search")
            
            # Try searching across multiple collections
            all_results = []
            search_successful = False
            combined_total = 0
            
            for collection in self.collections:
                try:
                    api_url = f"{self.base_url}/search/{collection}"
                    
                    # Correct headers for GET request (no Content-Type needed)
                    headers = {
                        'Authorization': f'ApiKey {self.api_key}'
                    }
                    
                    # Try different query formats for better matching
                    queries = [
                        entity_name,  # Original name
                        f'"{entity_name}"',  # Exact phrase search
                        entity_name.replace(',', '').strip(),  # Remove comma
                        entity_name.replace(' ', ' AND ').strip()  # AND operator
                    ]
                    
                    # For entity IDs, also try searching by ID field
                    if self._is_entity_id(entity_name):
                        queries.extend([
                            f'wikidataId:{entity_name}',
                            f'id:{entity_name}',
                            f'referents:{entity_name}',
                            f'identifiers:{entity_name}',
                            f'properties.id:{entity_name}',
                            f'properties.wikidataId:{entity_name}',
                            f'properties.referents:{entity_name}',
                            f'properties.identifiers:{entity_name}',
                            f'properties.datasets.id:{entity_name}',
                            f'properties.datasets.wikidataId:{entity_name}',
                            f'properties.datasets.referents:{entity_name}',
                            f'properties.datasets.identifiers:{entity_name}'
                        ])
                    
                    for query in queries:
                        params = {
                            'q': query.strip(),
                            'limit': 20
                        }
                        
                        # Add schema filter for better results
                        if collection == 'default':
                            # Don't restrict schema for default collection
                            pass
                        else:
                            # For specific collections, try both Person and LegalEntity
                            for schema in ['Person', 'LegalEntity']:
                                search_params = params.copy()
                                search_params['schema'] = schema
                                
                                logger.info(f"Searching OpenSanctions {collection} collection for: {query} (schema: {schema})")
                                
                                response = requests.get(
                                    api_url,
                                    headers=headers,
                                    params=search_params,
                                    timeout=30
                                )
                                
                                if response.status_code == 401:
                                    logger.error("OpenSanctions API authentication failed - invalid API key")
                                    return {
                                        'success': False,
                                        'error': 'OpenSanctions API authentication failed - invalid API key',
                                        'data': None,
                                        'total_results': 0
                                    }
                                
                                if response.status_code == 403:
                                    logger.error("OpenSanctions API access forbidden - check your subscription")
                                    return {
                                        'success': False,
                                        'error': 'OpenSanctions API access forbidden - check your subscription',
                                        'data': None,
                                        'total_results': 0
                                    }
                                
                                if response.status_code == 429:
                                    logger.error("OpenSanctions API rate limit exceeded")
                                    return {
                                        'success': False,
                                        'error': 'OpenSanctions API rate limit exceeded for this month. Please try again later or upgrade your subscription.',
                                        'data': None,
                                        'total_results': 0
                                    }
                                
                                response.raise_for_status()
                                data = response.json()
                                
                                # Check if we got results
                                total_results = data.get('total', {})
                                if isinstance(total_results, dict):
                                    total_count = total_results.get('value', 0)
                                else:
                                    total_count = total_results or 0
                                    
                                if total_count > 0:
                                    logger.info(f"OpenSanctions API found {total_count} results in {collection} collection for query: {query} (schema: {schema})")
                                    results = data.get('results', [])
                                    all_results.extend(results)
                                    combined_total += total_count
                                    search_successful = True
                                    
                                    # If we found good results, break out of schema loop
                                    if len(results) >= 3:
                                        break
                        
                        # For default collection, search without schema restriction
                        if collection == 'default':
                            logger.info(f"Searching OpenSanctions {collection} collection for: {query}")
                            
                            response = requests.get(
                                api_url,
                                headers=headers,
                                params=params,
                                timeout=30
                            )
                            
                            if response.status_code == 401:
                                logger.error("OpenSanctions API authentication failed - invalid API key")
                                return {
                                    'success': False,
                                    'error': 'OpenSanctions API authentication failed - invalid API key',
                                    'data': None,
                                    'total_results': 0
                                }
                            
                            if response.status_code == 403:
                                logger.error("OpenSanctions API access forbidden - check your subscription")
                                return {
                                    'success': False,
                                    'error': 'OpenSanctions API access forbidden - check your subscription',
                                    'data': None,
                                    'total_results': 0
                                }
                            
                            if response.status_code == 429:
                                logger.error("OpenSanctions API rate limit exceeded")
                                return {
                                    'success': False,
                                    'error': 'OpenSanctions API rate limit exceeded for this month. Please try again later or upgrade your subscription.',
                                    'data': None,
                                    'total_results': 0
                                }
                            
                            response.raise_for_status()
                            data = response.json()
                            
                            # Check if we got results
                            total_results = data.get('total', {})
                            if isinstance(total_results, dict):
                                total_count = total_results.get('value', 0)
                            else:
                                total_count = total_results or 0
                                
                            if total_count > 0:
                                logger.info(f"OpenSanctions API found {total_count} results in {collection} collection for query: {query}")
                                results = data.get('results', [])
                                all_results.extend(results)
                                combined_total += total_count
                                search_successful = True
                        
                        # If we found results with this query, try next collection
                        if search_successful and len(all_results) >= 5:
                            break
                    
                    # If we found enough results, no need to search other collections
                    if search_successful and len(all_results) >= 10:
                        break
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error searching {collection} collection: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error searching {collection} collection: {e}")
                    continue
            
            if search_successful:
                # Remove duplicates while preserving order
                seen_ids = set()
                unique_results = []
                for result in all_results:
                    result_id = result.get('id')
                    if result_id and result_id not in seen_ids:
                        seen_ids.add(result_id)
                        unique_results.append(result)
                
                # Create combined response
                combined_data = {
                    'results': unique_results[:10],  # Limit to top 10 unique results
                    'total': {'value': len(unique_results), 'relation': 'eq'},
                    'limit': 10,
                    'offset': 0,
                    'facets': {
                        'countries': {'label': 'countries', 'values': []},
                        'datasets': {'label': 'datasets', 'values': []},
                        'topics': {'label': 'topics', 'values': []}
                    }
                }
                
                logger.info(f"OpenSanctions API call successful for: {entity_name} (Total unique: {len(unique_results)})")
                return {
                    'success': True,
                    'data': combined_data,
                    'total_results': len(unique_results),
                    'error': None
                }
            else:
                logger.info(f"No results found in OpenSanctions for: {entity_name}")
                return {
                    'success': True,
                    'data': {
                        'results': [],
                        'total': {'value': 0, 'relation': 'eq'},
                        'limit': 10,
                        'offset': 0,
                        'facets': {
                            'countries': {'label': 'countries', 'values': []},
                            'datasets': {'label': 'datasets', 'values': []},
                            'topics': {'label': 'topics', 'values': []}
                        }
                    },
                    'total_results': 0,
                    'error': None
                }
            
        except Exception as e:
            logger.error(f"OpenSanctions API error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'total_results': 0
            }
    
    def _is_entity_id(self, entity_name):
        """Check if the entity name looks like an entity ID (WikiData format Q followed by digits)"""
        if not entity_name:
            return False
        
        # WikiData ID format: Q followed by digits
        wikidata_pattern = re.match(r'^Q\d+$', entity_name.strip())
        
        # Other common ID patterns
        other_id_patterns = [
            r'^[A-Z]{2,}\d+$',  # Letters followed by digits (e.g., OFAC-12345)
            r'^\d+$',  # Pure numeric IDs
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',  # UUID format
            r'^[a-f0-9]{40}$',  # SHA-1 hash format (40 characters)
            r'^[a-f0-9]{32}$',  # MD5 hash format (32 characters)
            r'^[a-f0-9]{64}$',  # SHA-256 hash format (64 characters)
            r'^[a-z]+-[a-f0-9]{40}$',  # Prefix-hash format (e.g., zafic-e392bce1897e8f51ceeb9cf5f54eac318ac6b735)
            r'^[a-z]+-[a-f0-9]{32}$',  # Prefix-MD5 format
            r'^[a-z]+-[a-f0-9]{64}$',  # Prefix-SHA256 format
            r'^[A-Za-z]+-\d+$',  # Prefix-numeric format (e.g., OFAC-12345)
            r'^[A-Za-z]+-[A-Za-z0-9]+$',  # General prefix-alphanumeric format
        ]
        
        if wikidata_pattern:
            return True
        
        for pattern in other_id_patterns:
            if re.match(pattern, entity_name.strip()):
                return True
        
        return False
    
    def _get_entity_by_id(self, entity_id):
        """Attempt to get entity data directly by ID"""
        try:
            headers = {
                'Authorization': f'ApiKey {self.api_key}'
            }
            
            # Try the entities endpoint directly
            entity_url = f"{self.base_url}/entities/{entity_id}"
            
            logger.info(f"Attempting direct entity retrieval: {entity_url}")
            
            response = requests.get(
                entity_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 404:
                logger.info(f"Entity {entity_id} not found via direct lookup")
                return {
                    'success': True,
                    'data': {'results': []},
                    'total_results': 0,
                    'error': None
                }
            
            if response.status_code == 401:
                logger.error("OpenSanctions API authentication failed - invalid API key")
                return {
                    'success': False,
                    'error': 'OpenSanctions API authentication failed - invalid API key',
                    'data': None,
                    'total_results': 0
                }
            
            if response.status_code == 403:
                logger.error("OpenSanctions API access forbidden - check your subscription")
                return {
                    'success': False,
                    'error': 'OpenSanctions API access forbidden - check your subscription',
                    'data': None,
                    'total_results': 0
                }
            
            if response.status_code == 429:
                logger.error("OpenSanctions API rate limit exceeded")
                return {
                    'success': False,
                    'error': 'OpenSanctions API rate limit exceeded for this month. Please try again later or upgrade your subscription.',
                    'data': None,
                    'total_results': 0
                }
            
            response.raise_for_status()
            entity_data = response.json()
            
            # Format response to match search API format
            formatted_data = {
                'results': [entity_data],
                'total': {'value': 1, 'relation': 'eq'},
                'limit': 1,
                'offset': 0,
                'facets': {
                    'countries': {'label': 'countries', 'values': []},
                    'datasets': {'label': 'datasets', 'values': []},
                    'topics': {'label': 'topics', 'values': []}
                }
            }
            
            logger.info(f"Direct entity retrieval successful for: {entity_id}")
            return {
                'success': True,
                'data': formatted_data,
                'total_results': 1,
                'error': None
            }
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Direct entity retrieval failed for {entity_id}: {e}")
            return {
                'success': True,
                'data': {'results': []},
                'total_results': 0,
                'error': None
            }
        except Exception as e:
            logger.error(f"Unexpected error in direct entity retrieval for {entity_id}: {e}")
            return {
                'success': True,
                'data': {'results': []},
                'total_results': 0,
                'error': None
            }
    
    def is_configured(self):
        """Check if OpenSanctions API is properly configured"""
        return bool(self.api_key) 