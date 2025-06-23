import time
import logging
import asyncio
import concurrent.futures
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
        # Thread pool for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    
    def process_entity(self, entity_name: str) -> Dict:
        """Process a single entity through the enhanced workflow with optimizations"""
        logger.info(f"Processing entity: {entity_name}")
        start_time = time.time()
        
        # Step 1: Check Redis cache (re-enabled for performance)
        cached_result = self.cache_service.get(entity_name)
        if cached_result:
            cache_time = time.time() - start_time
            logger.info(f"Returning cached result for: {entity_name} in {cache_time:.2f}s")
            return cached_result
        
        # Step 2: Run OpenSanctions and Web Search in parallel
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks to run in parallel
                opensanctions_future = executor.submit(self.opensanctions_service.search_entity, entity_name)
                search_future = executor.submit(self._fast_web_search, entity_name)
                
                # Wait for both to complete with timeout
                opensanctions_result = opensanctions_future.result(timeout=15)
                web_search_result = search_future.result(timeout=15)
                
        except concurrent.futures.TimeoutError:
            logger.warning(f"Timeout processing entity: {entity_name}")
            # Return partial results if timeout
            opensanctions_result = {"success": False, "error": "Timeout", "data": None}
            web_search_result = {"success": False, "error": "Timeout", "ranked_results": []}
        except Exception as e:
            logger.error(f"Error in parallel processing for {entity_name}: {e}")
            # Fallback to sequential processing
            opensanctions_result = self.opensanctions_service.search_entity(entity_name)
            web_search_result = self.search_service.intelligent_search(entity_name, opensanctions_result)
        
        # Step 3: Create comprehensive result
        comprehensive_result = self._create_comprehensive_result(
            entity_name, opensanctions_result, web_search_result
        )
        
        # Step 4: Cache the result
        self.cache_service.set(entity_name, comprehensive_result)
        
        processing_time = time.time() - start_time
        logger.info(f"Processed entity {entity_name} in {processing_time:.2f}s")
        
        return comprehensive_result
    
    def _fast_web_search(self, entity_name: str) -> Dict:
        """Optimized web search with reduced queries and better targeting"""
        try:
            # Use only the most effective search queries (reduced from 5 to 2)
            if self.search_service.serper_api_key:
                # More specific search query to avoid generic results
                primary_query = f'"{entity_name}" (sanctions OR wanted OR investigation OR enforcement OR "financial crime" OR "regulatory action")'
                result = self.search_service._search_with_serper(primary_query, entity_name)
                if result.get('success'):
                    return self.search_service._merge_and_rank_results([result], entity_name, None)
            
            return {
                'success': False,
                'error': 'No search provider configured',
                'ranked_results': []
            }
        except Exception as e:
            logger.error(f"Fast web search error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'ranked_results': []
            }
    
    def process_multiple_entities(self, entity_names: List[str]) -> List[Dict]:
        """Process multiple entities efficiently"""
        results = []
        
        for entity_name in entity_names:
            if not isinstance(entity_name, str) or not entity_name.strip():
                results.append({
                    'api_version': '2.0.0',
                    'entity': {
                        'name': entity_name
                    },
                    'result': {
                        'found': False,
                        'results': [],
                        'total_results': 0,
                        'summary': 'Invalid entity name',
                        'status': 'failed',
                        'timestamp': int(time.time())
                    },
                    'success': False
                })
                continue
            
            try:
                result = self.process_entity(entity_name.strip())
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing entity {entity_name}: {e}")
                results.append({
                    'api_version': '2.0.0',
                    'entity': {
                        'name': entity_name
                    },
                    'result': {
                        'found': False,
                        'results': [],
                        'total_results': 0,
                        'summary': f'Processing error: {str(e)}',
                        'status': 'failed',
                        'timestamp': int(time.time())
                    },
                    'success': False
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
                'api_version': '2.0.0',
                'entity': {
                    'name': entity_id
                },
                'result': {
                    'found': False,
                    'results': [],
                    'total_results': 0,
                    'summary': f'Processing error: {str(e)}',
                    'status': 'failed',
                    'timestamp': int(time.time())
                },
                'success': False
            }
    
    def _create_comprehensive_result(self, entity_name: str, opensanctions_result: Dict, web_search_result: Dict) -> Dict:
        """Create simplified unified result combining OpenSanctions and web search data"""
        start_time = time.time()
        
        combined_results = []
        total_found = 0
        sources_found = []
        opensanctions_count = 0
        
        # Process OpenSanctions results
        opensanctions_found = False
        opensanctions_error = None
        
        if opensanctions_result.get('success') and opensanctions_result.get('data'):
            results = opensanctions_result['data'].get('results', [])
            opensanctions_total = opensanctions_result.get('total_results', 0)
            # Ensure opensanctions_total is a number
            if isinstance(opensanctions_total, (int, float)):
                opensanctions_total = int(opensanctions_total)
            else:
                opensanctions_total = 0
                
            if results and opensanctions_total > 0:
                opensanctions_found = True
                opensanctions_count = opensanctions_total
                sources_found.append(f"OpenSanctions ({opensanctions_total} records)")
                
                # Add OpenSanctions results to combined list (limit to 2 for faster processing)
                for i, result in enumerate(results[:2]):  # Reduced from 3 to 2
                    # Handle different OpenSanctions response structures
                    if isinstance(result, dict):
                        # Try to extract properties from different possible locations
                        properties = result.get('properties', {})
                        if not properties:
                            # If no properties, try direct fields
                            properties = result
                        
                        # Extract key information with fallbacks
                        name = properties.get('name', [])
                        if isinstance(name, list):
                            name = name[0] if name else entity_name
                        else:
                            name = name or entity_name
                        
                        gender = properties.get('gender', [])
                        if isinstance(gender, list):
                            gender = gender[0] if gender else 'Not available'
                        else:
                            gender = gender or 'Not available'
                        
                        birth_date = properties.get('birthDate', [])
                        if isinstance(birth_date, list):
                            birth_date = birth_date[0] if birth_date else 'Not available'
                        else:
                            birth_date = birth_date or 'Not available'
                        
                        country = properties.get('country', [])
                        if isinstance(country, list):
                            country = country[0] if country else 'Not available'
                        else:
                            country = country or 'Not available'
                        
                        source_url = properties.get('sourceUrl', [])
                        if isinstance(source_url, list):
                            source_url = source_url[0] if source_url else ''
                        else:
                            source_url = source_url or ''
                        
                        notes = properties.get('notes', [])
                        if isinstance(notes, list):
                            description = notes[0] if notes else 'No description available'
                        else:
                            description = notes or 'No description available'
                        
                        datasets = result.get('datasets', [])
                        source_name = datasets[0] if datasets else 'OpenSanctions'
                        
                        # Create result object with opensanctions and web_reference sections
                        result_obj = {
                            'opensanctions': {
                                'birth_date': birth_date,
                                'country': country,
                                'description': description,
                                'gender': gender,
                                'name': name,
                                'relevance': 'high',
                                'source': 'OpenSanctions',
                                'source_link': source_url,
                                'source_name': source_name,
                                'type': 'sanctions_record'
                            }
                        }
                        
                        # Add related web search results for this OpenSanctions entity
                        if web_search_result.get('success'):
                            ranked_results = web_search_result.get('ranked_results', [])
                            if ranked_results and i < len(ranked_results):
                                # Add corresponding web search result for this OpenSanctions result
                                web_result = ranked_results[i]
                                result_obj['web_reference'] = {
                                    'description': web_result.get('snippet', ''),
                                    'relevance': 'high' if isinstance(web_result.get('relevance_score'), (int, float)) and web_result.get('relevance_score', 0) > 0.8 else 'medium',
                                    'source': 'Web Search',
                                    'source_link': web_result.get('link', ''),
                                    'source_name': web_result.get('source_name', web_result.get('domain', '')),
                                    'title': web_result.get('title', ''),
                                    'type': 'web_reference'
                                }
                            elif ranked_results:
                                # If we have web results but not enough for each OpenSanctions result, use the first one
                                web_result = ranked_results[0]
                                result_obj['web_reference'] = {
                                    'description': web_result.get('snippet', ''),
                                    'relevance': 'high' if isinstance(web_result.get('relevance_score'), (int, float)) and web_result.get('relevance_score', 0) > 0.8 else 'medium',
                                    'source': 'Web Search',
                                    'source_link': web_result.get('link', ''),
                                    'source_name': web_result.get('source_name', web_result.get('domain', '')),
                                    'title': web_result.get('title', ''),
                                    'type': 'web_reference'
                                }
                        
                        combined_results.append(result_obj)
                    
        elif not opensanctions_result.get('success'):
            opensanctions_error = opensanctions_result.get('error', 'Unknown OpenSanctions API error')
        
        # If no OpenSanctions results but web search has results, add them separately
        if not opensanctions_found and web_search_result.get('success'):
            ranked_results = web_search_result.get('ranked_results', [])
            web_search_total = web_search_result.get('total_results', 0)
            # Ensure web_search_total is a number
            if isinstance(web_search_total, (int, float)):
                web_search_total = int(web_search_total)
            else:
                web_search_total = 0
                
            if ranked_results and web_search_total > 0:
                sources_found.append(f"Web search ({web_search_total} results)")
                
                # Add web search results (limit to 3 when no OpenSanctions data)
                for result in ranked_results[:3]:  # Reduced from 5 to 3
                    combined_results.append({
                        'web_reference': {
                            'description': result.get('snippet', ''),
                            'relevance': 'high' if isinstance(result.get('relevance_score'), (int, float)) and result.get('relevance_score', 0) > 0.8 else 'medium',
                            'source': 'Web Search',
                            'source_link': result.get('link', ''),
                            'source_name': result.get('source_name', result.get('domain', '')),
                            'title': result.get('title', ''),
                            'type': 'web_reference'
                        }
                    })
        
        total_found = len(combined_results)
        
        # Create final result structure matching the desired format
        final_result = {
            'api_version': '2.0.0',
            'entity': {
                'name': entity_name
            },
            'result': {
                'found': total_found > 0,
                'results': combined_results,
                'total_results': total_found,
                'summary': self._generate_simple_message(entity_name, sources_found, opensanctions_error, opensanctions_count),
                'status': 'completed',
                'timestamp': int(time.time())
            },
            'success': True
        }
        
        processing_time = time.time() - start_time
        logger.info(f"Result compilation for {entity_name} completed in {processing_time:.3f}s")
        
        return final_result
    
    def _generate_simple_message(self, entity_name: str, sources_found: List[str], opensanctions_error: str = None, opensanctions_count: int = 0) -> str:
        """Generate simple result message"""
        if opensanctions_error:
            return f"Search completed with API limitations. Found {len(sources_found)} source(s)."
        elif sources_found:
            # If we have OpenSanctions results, prioritize that in the summary
            if opensanctions_count > 0:
                return f"Found in OpenSanctions ({opensanctions_count} records)"
            else:
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