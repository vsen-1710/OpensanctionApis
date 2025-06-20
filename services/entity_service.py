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
    
    def process_entity_by_id(self, entity_id: str) -> Dict:
        """Process a single entity by OpenSanctions entity ID"""
        logger.info(f"Processing entity by ID: {entity_id}")
        
        try:
            # Step 1: Call OpenSanctions API with entity ID
            opensanctions_result = self.opensanctions_service.search_entity(entity_id)
            
            # Step 2: Use OpenSanctions data to enhance web search
            web_search_result = self.search_service.intelligent_search(entity_id, opensanctions_result)
            
            # Step 3: Create comprehensive result
            comprehensive_result = self._create_comprehensive_result(
                entity_id, opensanctions_result, web_search_result
            )
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Error processing entity ID {entity_id}: {e}")
            return {
                'entity_id': entity_id,
                'error': f'Processing error: {str(e)}',
                'timestamp': int(time.time()),
                'processing_status': 'failed'
            }
    
    def _create_comprehensive_result(self, entity_name: str, opensanctions_result: Dict, web_search_result: Dict) -> Dict:
        """Create simplified unified result combining OpenSanctions and web search data"""
        
        combined_results = []
        total_found = 0
        sources_found = []
        
        # Process OpenSanctions results
        opensanctions_found = False
        opensanctions_error = None
        
        if opensanctions_result.get('success') and opensanctions_result.get('data'):
            results = opensanctions_result['data'].get('results', [])
            opensanctions_total = opensanctions_result.get('total_results', 0)
            if results and opensanctions_total > 0:
                opensanctions_found = True
                sources_found.append(f"OpenSanctions ({opensanctions_total} records)")
                
                # Add OpenSanctions results to combined list
                for result in results[:3]:  # Limit to top 3 results
                    properties = result.get('properties', {})
                    
                    # Extract key information
                    name = properties.get('name', [])
                    name = name[0] if name else entity_name
                    
                    gender = properties.get('gender', [])
                    gender = gender[0] if gender else 'Not available'
                    
                    birth_date = properties.get('birthDate', [])
                    birth_date = birth_date[0] if birth_date else 'Not available'
                    
                    country = properties.get('country', [])
                    country = country[0] if country else 'Not available'
                    
                    source_url = properties.get('sourceUrl', [])
                    source_url = source_url[0] if source_url else ''
                    
                    notes = properties.get('notes', [])
                    description = notes[0] if notes else 'No description available'
                    
                    datasets = result.get('datasets', [])
                    source_name = datasets[0] if datasets else 'OpenSanctions'
                    
                    combined_results.append({
                        'source': 'OpenSanctions',
                        'type': 'sanctions_record',
                        'name': name,
                        'birth_date': birth_date,
                        'gender': gender,
                        'country': country,
                        'description': description,
                        'source_link': source_url,
                        'source_name': source_name,
                        'relevance': 'high'
                    })
                    
        elif not opensanctions_result.get('success'):
            opensanctions_error = opensanctions_result.get('error', 'Unknown OpenSanctions API error')
        
        # Process web search results
        web_search_found = False
        
        if web_search_result.get('success'):
            ranked_results = web_search_result.get('ranked_results', [])
            web_search_total = web_search_result.get('total_results', 0)
            if ranked_results and web_search_total > 0:
                web_search_found = True
                sources_found.append(f"Web search ({web_search_total} results)")
                
                # Add web search results to combined list
                for result in ranked_results[:3]:  # Limit to top 3 results
                    combined_results.append({
                        'source': 'Web Search',
                        'type': 'web_reference',
                        'title': result.get('title', ''),
                        'description': result.get('snippet', ''),
                        'source_link': result.get('link', ''),
                        'source_name': result.get('domain', ''),
                        'relevance': 'high' if result.get('relevance_score', 0) > 0.8 else 'medium'
                    })
        
        total_found = len(combined_results)
        
        # Generate suggestions
        suggestions = []
        if opensanctions_found:
            suggestions.append("Entity found in sanctions database - Enhanced due diligence recommended")
        if web_search_found and any('wanted' in r.get('description', '').lower() for r in combined_results):
            suggestions.append("Potential law enforcement interest detected - Verify through official channels")
        if not opensanctions_found and not web_search_found:
            suggestions.append("No records found - Consider searching with name variations")
        if total_found > 0:
            suggestions.append("Review all sources for comprehensive risk assessment")
        
        # Create simplified response
        return {
            'found': opensanctions_found or web_search_found,
            'summary': self._generate_simple_message(entity_name, sources_found, opensanctions_error),
            'total_results': total_found,
            'results': combined_results,
            'recommendations': suggestions[:3],  # Limit to top 3 suggestions
            'timestamp': int(time.time()),
            'status': 'completed'
        }
    
    def _generate_simple_message(self, entity_name: str, sources_found: List[str], opensanctions_error: str = None) -> str:
        """Generate simple result message"""
        if opensanctions_error:
            return f"Search completed with API limitations. Found {len(sources_found)} source(s)."
        elif sources_found:
            sources_text = " and ".join(sources_found)
            return f"Found in {sources_text}"
        else:
            return "No records found in available databases"
    
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