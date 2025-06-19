import requests
import logging
import json
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.serper_api_key = Config.SERPER_API_KEY
        self.serper_api_url = Config.SERPER_API_URL
        self.trusted_domains = Config.TRUSTED_DOMAINS
    
    def intelligent_search(self, entity_name: str, opensanctions_data: Optional[Dict] = None) -> Dict:
        """Enhanced search that uses OpenSanctions data to create more accurate search queries"""
        try:
            # Generate intelligent search queries based on OpenSanctions data
            search_queries = self._generate_intelligent_queries(entity_name, opensanctions_data)
            
            # Perform searches and rank results
            all_results = []
            for query_data in search_queries:
                if self.serper_api_key:
                    result = self._search_with_serper(query_data['query'], entity_name)
                    if result.get('success'):
                        result['query_context'] = query_data['context']
                        result['relevance_score'] = query_data['relevance_score']
                        all_results.append(result)
            
            # Merge and rank all results
            return self._merge_and_rank_results(all_results, entity_name, opensanctions_data)
                
        except Exception as e:
            logger.error(f"Intelligent search error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': [],
                'ranked_results': []
            }
    
    def _generate_intelligent_queries(self, entity_name: str, opensanctions_data: Optional[Dict] = None) -> List[Dict]:
        """Generate multiple intelligent search queries based on OpenSanctions findings"""
        queries = []
        
        # Base query with high relevance
        queries.append({
            'query': f'"{entity_name}" sanctions compliance regulatory',
            'context': 'General sanctions and compliance check',
            'relevance_score': 0.8
        })
        
        # If we have OpenSanctions data, create targeted queries
        if opensanctions_data and opensanctions_data.get('success') and opensanctions_data.get('data'):
            os_data = opensanctions_data['data']
            results = os_data.get('results', [])
            
            if results:
                # Extract information from OpenSanctions results
                for result in results[:3]:  # Top 3 results
                    countries = result.get('countries', [])
                    datasets = result.get('datasets', [])
                    topics = result.get('topics', [])
                    
                    # Country-specific search
                    if countries:
                        for country in countries[:2]:  # Top 2 countries
                            queries.append({
                                'query': f'"{entity_name}" {country} sanctions "law enforcement" OR investigation',
                                'context': f'Country-specific search for {country}',
                                'relevance_score': 0.9
                            })
                    
                    # Dataset-specific search
                    if datasets:
                        for dataset in datasets[:2]:  # Top 2 datasets
                            if 'wanted' in dataset.lower():
                                queries.append({
                                    'query': f'"{entity_name}" wanted fugitive "law enforcement"',
                                    'context': 'Wanted persons database search',
                                    'relevance_score': 0.95
                                })
                            elif 'sanction' in dataset.lower():
                                queries.append({
                                    'query': f'"{entity_name}" international sanctions OFAC EU',
                                    'context': 'International sanctions search',
                                    'relevance_score': 0.95
                                })
                    
                    # Topic-specific search
                    if topics:
                        for topic in topics[:2]:  # Top 2 topics
                            queries.append({
                                'query': f'"{entity_name}" {topic} "compliance risk"',
                                'context': f'Topic-specific search for {topic}',
                                'relevance_score': 0.85
                            })
        
        # Additional intelligence-based queries
        name_parts = entity_name.replace(',', '').split()
        if len(name_parts) >= 2:
            # Search with name variations
            queries.append({
                'query': f'"{" ".join(name_parts)}" OR "{name_parts[-1]}, {" ".join(name_parts[:-1])}" enforcement',
                'context': 'Name variation search',
                'relevance_score': 0.75
            })
        
        # Financial crime and AML search
        queries.append({
            'query': f'"{entity_name}" "anti money laundering" OR AML OR "financial crime"',
            'context': 'Financial crime and AML search',
            'relevance_score': 0.8
        })
        
        return queries[:5]  # Limit to top 5 queries
    
    def _search_with_serper(self, search_query: str, entity_name: str) -> Dict:
        """Enhanced Serper search with intelligent domain handling"""
        try:
            # First try with trusted domain restrictions
            domain_query = " OR ".join([f"site:{domain}" for domain in self.trusted_domains])
            enhanced_query = f"({search_query}) AND ({domain_query})"
            
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': enhanced_query,
                'num': 5,
                'gl': 'us',
                'hl': 'en',
                'type': 'search'
            }
            
            response = requests.post(
                self.serper_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check if we got results from trusted domains
            organic_results = data.get('organic', [])
            
            if organic_results:
                logger.info(f"Enhanced Serper API call successful with trusted domains for: {entity_name}")
                return {
                    'success': True,
                    'data': data,
                    'search_query': enhanced_query,
                    'provider': 'serper',
                    'search_type': 'trusted_domains'
                }
            else:
                # No results from trusted domains, try broader search
                logger.info(f"No results from trusted domains for {entity_name}, trying broader search")
                
                # Fallback to search without domain restrictions but with compliance-focused terms
                fallback_query = f'"{entity_name}" (sanctions OR compliance OR "law enforcement" OR wanted OR investigation OR regulatory)'
                
                fallback_payload = {
                    'q': fallback_query,
                    'num': 10,  # Get more results for broader search
                    'gl': 'us',
                    'hl': 'en',
                    'type': 'search'
                }
                
                fallback_response = requests.post(
                    self.serper_api_url,
                    headers=headers,
                    json=fallback_payload,
                    timeout=30
                )
                
                fallback_response.raise_for_status()
                fallback_data = fallback_response.json()
                
                logger.info(f"Fallback Serper API call successful for: {entity_name}")
                return {
                    'success': True,
                    'data': fallback_data,
                    'search_query': fallback_query,
                    'provider': 'serper',
                    'search_type': 'fallback_broader'
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Enhanced Serper API error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'search_query': search_query
            }
    
    def _merge_and_rank_results(self, all_results: List[Dict], entity_name: str, opensanctions_data: Optional[Dict]) -> Dict:
        """Merge and rank all search results by relevance"""
        try:
            merged_results = []
            seen_urls = set()
            
            # Sort results by relevance score
            all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            for result in all_results:
                if not result.get('success') or not result.get('data'):
                    continue
                
                organic_results = result['data'].get('organic', [])
                for organic in organic_results:
                    url = organic.get('link', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        
                        # Calculate relevance score for this specific result
                        relevance = self._calculate_result_relevance(
                            organic, entity_name, opensanctions_data, result.get('relevance_score', 0.5)
                        )
                        
                        enhanced_result = {
                            'title': organic.get('title', ''),
                            'link': url,
                            'snippet': organic.get('snippet', ''),
                            'relevance_score': relevance,
                            'query_context': result.get('query_context', 'General search'),
                            'domain': self._extract_domain(url),
                            'is_trusted_source': self._is_trusted_domain(url)
                        }
                        merged_results.append(enhanced_result)
            
            # Sort by relevance score
            merged_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Generate search suggestions
            suggestions = self._generate_search_suggestions(entity_name, opensanctions_data, merged_results)
            
            return {
                'success': True,
                'total_results': len(merged_results),
                'ranked_results': merged_results[:10],  # Top 10 results
                'suggestions': suggestions,
                'search_strategy': 'intelligent_opensanctions_enhanced'
            }
            
        except Exception as e:
            logger.error(f"Error merging and ranking results for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': [],
                'ranked_results': []
            }
    
    def _calculate_result_relevance(self, result: Dict, entity_name: str, opensanctions_data: Optional[Dict], base_score: float) -> float:
        """Calculate relevance score for a search result"""
        score = base_score
        
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        content = f"{title} {snippet}"
        
        # Name matching - give higher score for exact name matches
        entity_name_lower = entity_name.lower()
        if entity_name_lower in content:
            score += 0.2
        
        name_parts = entity_name.lower().replace(',', '').split()
        matching_parts = 0
        for part in name_parts:
            if len(part) > 2 and part in content:
                matching_parts += 1
                score += 0.1
        
        # Bonus for matching all name parts
        if matching_parts == len(name_parts) and len(name_parts) > 1:
            score += 0.15
        
        # High-value keywords for compliance and law enforcement
        high_value_keywords = ['sanctions', 'wanted', 'fugitive', 'enforcement', 'investigation', 'compliance', 'regulatory', 'aml', 'laundering']
        for keyword in high_value_keywords:
            if keyword in content:
                score += 0.15
        
        # OpenSanctions context matching
        if opensanctions_data and opensanctions_data.get('success'):
            os_results = opensanctions_data.get('data', {}).get('results', [])
            for os_result in os_results:
                countries = [c.lower() for c in os_result.get('countries', [])]
                datasets = [d.lower() for d in os_result.get('datasets', [])]
                topics = [t.lower() for t in os_result.get('topics', [])]
                
                # Country matching
                for country in countries:
                    if country in content:
                        score += 0.2
                
                # Dataset matching
                for dataset in datasets:
                    if any(keyword in dataset for keyword in ['wanted', 'sanction']):
                        if any(keyword in content for keyword in ['wanted', 'sanction']):
                            score += 0.25
                
                # Topic matching
                for topic in topics:
                    if topic in content:
                        score += 0.15
        
        # Trusted domain bonus (but don't penalize non-trusted domains)
        if self._is_trusted_domain(result.get('link', '')):
            score += 0.1
        
        # Penalty for very short snippets (likely not relevant)
        if len(snippet) < 50:
            score *= 0.8
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_search_suggestions(self, entity_name: str, opensanctions_data: Optional[Dict], results: List[Dict]) -> List[Dict]:
        """Generate intelligent search suggestions based on findings"""
        suggestions = []
        
        # Analyze what we found
        has_sanctions = any('sanction' in r['snippet'].lower() for r in results[:5])
        has_wanted = any('wanted' in r['snippet'].lower() or 'fugitive' in r['snippet'].lower() for r in results[:5])
        has_investigation = any('investigation' in r['snippet'].lower() for r in results[:5])
        
        # Generate contextual suggestions
        if opensanctions_data and opensanctions_data.get('success'):
            total_results = opensanctions_data.get('total_results', 0)
            
            if total_results > 0:
                suggestions.append({
                    'type': 'alert',
                    'title': 'Entity Found in OpenSanctions Database',
                    'description': f'This entity appears in {total_results} sanctions/compliance records. Consider enhanced due diligence.',
                    'action': 'review_detailed_records',
                    'priority': 'high'
                })
                
                if has_wanted:
                    suggestions.append({
                        'type': 'warning',
                        'title': 'Potential Law Enforcement Interest',
                        'description': 'Web search indicates possible law enforcement involvement. Verify through official channels.',
                        'action': 'contact_authorities',
                        'priority': 'critical'
                    })
            
            if has_sanctions and not total_results:
                suggestions.append({
                    'type': 'info',
                    'title': 'Sanctions-Related Content Found',
                    'description': 'Web search mentions sanctions but not found in OpenSanctions database. May be historical or indirect.',
                    'action': 'investigate_further',
                    'priority': 'medium'
                })
        
        if has_investigation:
            suggestions.append({
                'type': 'caution',
                'title': 'Investigation References Found',
                'description': 'Web search indicates ongoing or past investigations. Review for compliance implications.',
                'action': 'compliance_review',
                'priority': 'medium'
            })
        
        # Suggest additional searches
        if len(results) < 3:
            suggestions.append({
                'type': 'suggestion',
                'title': 'Limited Results Found',
                'description': 'Consider searching with name variations or alternative spellings.',
                'action': 'expand_search',
                'priority': 'low'
            })
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL is from a trusted domain"""
        domain = self._extract_domain(url)
        return any(trusted in domain for trusted in self.trusted_domains)
    
    def search_entity(self, entity_name: str):
        """Legacy method for backward compatibility"""
        return self.intelligent_search(entity_name)
    
    def is_configured(self):
        """Check if any search API is properly configured"""
        return bool(self.serper_api_key)
    
    def get_configured_providers(self):
        """Get list of configured search providers"""
        providers = []
        if self.serper_api_key:
            providers.append('serper')
        return providers 