import time
import logging
from typing import Dict, List, Optional
from .cache_service import CacheService
from .opensanctions_service import OpenSanctionsService
from .search_service import SearchService

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self):
        self.cache_service = CacheService()
        self.opensanctions_service = OpenSanctionsService()
        self.search_service = SearchService()
    
    def process_entity(self, entity_name: str) -> Dict:
        """Process a single entity through the enhanced workflow"""
        logger.info(f"Processing entity: {entity_name}")
        
        # Step 1: Check Redis cache (temporarily disabled)
        # cached_result = self.cache_service.get(entity_name)
        # if cached_result:
        #     logger.info(f"Returning cached result for: {entity_name}")
        #     return cached_result
        
        # Step 2: Call OpenSanctions API first
        opensanctions_result = self.opensanctions_service.search_entity(entity_name)
        
        # Step 3: Use OpenSanctions data to enhance web search
        web_search_result = self.search_service.intelligent_search(entity_name, opensanctions_result)
        
        # Step 4: Create comprehensive result
        comprehensive_result = self._create_comprehensive_result(
            entity_name, opensanctions_result, web_search_result
        )
        
        # Step 5: Cache the result (temporarily disabled)
        # self.cache_service.set(entity_name, comprehensive_result)
        
        return comprehensive_result
    
    def process_multiple_entities(self, entity_names: List[str]) -> List[Dict]:
        """Process multiple entities efficiently"""
        results = []
        
        for entity_name in entity_names:
            if not isinstance(entity_name, str) or not entity_name.strip():
                results.append({
                    'entity_name': entity_name,
                    'error': 'Invalid entity name',
                    'timestamp': int(time.time()),
                    'processing_status': 'failed'
                })
                continue
            
            try:
                result = self.process_entity(entity_name.strip())
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing entity {entity_name}: {e}")
                results.append({
                    'entity_name': entity_name,
                    'error': f'Processing error: {str(e)}',
                    'timestamp': int(time.time()),
                    'processing_status': 'failed'
                })
        
        return results
    
    def _create_comprehensive_result(self, entity_name: str, opensanctions_result: Dict, web_search_result: Dict) -> Dict:
        """Create comprehensive result including both OpenSanctions and web search data"""
        
        # Determine if OpenSanctions found any results
        opensanctions_found = False
        opensanctions_data = None
        opensanctions_total = 0
        
        if opensanctions_result.get('success') and opensanctions_result.get('data'):
            results = opensanctions_result['data'].get('results', [])
            opensanctions_total = opensanctions_result.get('total_results', 0)
            if results and opensanctions_total > 0:
                opensanctions_found = True
                opensanctions_data = opensanctions_result['data']
        
        # Process web search results
        web_search_found = False
        web_search_data = None
        web_search_total = 0
        
        if web_search_result.get('success'):
            ranked_results = web_search_result.get('ranked_results', [])
            web_search_total = web_search_result.get('total_results', 0)
            if ranked_results and web_search_total > 0:
                web_search_found = True
                web_search_data = {
                    'results': ranked_results,
                    'total_results': web_search_total,
                    'suggestions': web_search_result.get('suggestions', []),
                    'search_strategy': web_search_result.get('search_strategy', 'intelligent_search')
                }
        
        # Create comprehensive response
        return {
            'found': opensanctions_found or web_search_found,
            'message': self._generate_result_message(entity_name, opensanctions_found, web_search_found, opensanctions_total, web_search_total),
            'opensanctions': {
                'found': opensanctions_found,
                'total_results': opensanctions_total,
                'data': opensanctions_data,
                'error': opensanctions_result.get('error') if not opensanctions_result.get('success') else None
            },
            'web_search': {
                'found': web_search_found,
                'total_results': web_search_total,
                'data': web_search_data,
                'error': web_search_result.get('error') if not web_search_result.get('success') else None
            },
            'timestamp': int(time.time()),
            'processing_status': 'completed'
        }
    
    def _generate_result_message(self, entity_name: str, opensanctions_found: bool, web_search_found: bool, os_total: int, ws_total: int) -> str:
        """Generate appropriate result message based on findings"""
        if opensanctions_found and web_search_found:
            return f'{entity_name} found in OpenSanctions database ({os_total} records) and web search ({ws_total} results)'
        elif opensanctions_found:
            return f'{entity_name} found in OpenSanctions database ({os_total} records) but no relevant web search results'
        elif web_search_found:
            return f'{entity_name} not found in OpenSanctions database but found {ws_total} relevant web search results'
        else:
            return f'{entity_name} not found in OpenSanctions database or web search results'
    
    def get_health_status(self) -> Dict:
        """Get health status of all services"""
        return {
            'cache_connected': self.cache_service.is_connected(),
            'opensanctions_configured': self.opensanctions_service.is_configured(),
            'search_configured': self.search_service.is_configured(),
            'search_providers': self.search_service.get_configured_providers()
        }
    
    def clear_cache(self) -> bool:
        """Clear all cached data"""
        return self.cache_service.flush_cache() 