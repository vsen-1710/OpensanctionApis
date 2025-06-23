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
        """Enhanced search that uses OpenSanctions data to create more accurate search queries - optimized"""
        try:
            # For fast response, use only 1-2 targeted searches instead of 5
            if opensanctions_data and opensanctions_data.get('success') and opensanctions_data.get('data'):
                # If we have OpenSanctions data, use it for targeted search
                search_query = self._generate_smart_query(entity_name, opensanctions_data)
            else:
                # Simple general query for entities not in OpenSanctions
                search_query = f'"{entity_name}"'
            
            # Perform single optimized search
            if self.serper_api_key:
                result = self._search_with_serper(search_query, entity_name)
                if result.get('success'):
                    return self._merge_and_rank_results([result], entity_name, opensanctions_data)
            
            return {
                'success': False,
                'error': 'No search provider configured',
                'suggestions': [],
                'ranked_results': []
            }
                
        except Exception as e:
            logger.error(f"Intelligent search error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': [],
                'ranked_results': []
            }
    
    def _generate_smart_query(self, entity_name: str, opensanctions_data: Dict) -> str:
        """Generate a single smart query based on OpenSanctions findings"""
        base_query = f'"{entity_name}"'
        
        if opensanctions_data and opensanctions_data.get('success') and opensanctions_data.get('data'):
            os_data = opensanctions_data['data']
            results = os_data.get('results', [])
            
            if results:
                result = results[0]  # Use first result
                countries = result.get('countries', [])
                datasets = result.get('datasets', [])
                
                # Add most relevant context based on actual findings
                if 'wanted' in str(datasets).lower():
                    return f'{base_query} wanted fugitive "law enforcement" criminal'
                elif 'sanctions' in str(datasets).lower():
                    return f'{base_query} sanctions "financial crime" compliance investigation'
                elif countries:
                    return f'{base_query} {countries[0]} sanctions "regulatory action" investigation'
                else:
                    return f'{base_query} sanctions compliance "regulatory enforcement"'
        
        # For entities without OpenSanctions data, use more specific terms
        return f'{base_query} sanctions "enforcement action" "regulatory investigation" "financial crime"'
    
    def _search_with_serper(self, search_query: str, entity_name: str) -> Dict:
        """Enhanced Serper search with intelligent domain handling - optimized"""
        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            # Single search with reasonable timeout
            payload = {
                'q': search_query,
                'num': 5,  # Reduced from 10 to 5 for faster response
                'gl': 'us',
                'hl': 'en',
                'type': 'search'
            }
            
            response = requests.post(
                self.serper_api_url,
                headers=headers,
                json=payload,
                timeout=8  # Reduced timeout from 30 to 8 seconds
            )
            
            response.raise_for_status()
            data = response.json()
            
            organic_results = data.get('organic', [])
            
            if organic_results:
                logger.info(f"Serper API call successful for: {entity_name}")
                return {
                    'success': True,
                    'data': data,
                    'search_query': search_query,
                    'provider': 'serper',
                    'search_type': 'optimized'
                }
            else:
                logger.info(f"No results from Serper for {entity_name}")
                return {
                    'success': False,
                    'error': 'No search results found',
                    'data': None,
                    'search_query': search_query
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API error for {entity_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'search_query': search_query
            }
    
    def _merge_and_rank_results(self, all_results: List[Dict], entity_name: str, opensanctions_data: Optional[Dict]) -> Dict:
        """Merge and rank all search results by relevance - TRUSTED DOMAINS ONLY"""
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
                        
                        # Extract domain for source identification
                        domain = self._extract_domain(url)
                        is_trusted = self._is_trusted_domain(url)
                        
                        # ONLY INCLUDE TRUSTED DOMAINS - Simple fix as requested
                        if not is_trusted:
                            continue  # Skip all non-trusted domains
                        
                        # Calculate relevance score for this specific result
                        relevance = self._calculate_result_relevance(
                            organic, entity_name, opensanctions_data, result.get('relevance_score', 0.5)
                        )
                        
                        # For trusted domains, use a lower relevance threshold
                        if relevance >= 0.1:  # Lower threshold since we trust these domains
                            source_name = self._get_source_name(domain)
                            
                            enhanced_result = {
                                'title': organic.get('title', ''),
                                'link': url,
                                'snippet': organic.get('snippet', ''),
                                'relevance_score': relevance,
                                'query_context': result.get('query_context', 'General search'),
                                'domain': domain,
                                'source_name': source_name,
                                'is_trusted_source': True  # All results are now trusted
                            }
                            merged_results.append(enhanced_result)
            
            # Sort by relevance score
            merged_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Generate search suggestions only if we have meaningful results
            suggestions = self._generate_search_suggestions(entity_name, opensanctions_data, merged_results)
            
            return {
                'success': len(merged_results) > 0,  # Only success if we found trusted domain results
                'total_results': len(merged_results),
                'ranked_results': merged_results[:5],  # Top 5 most relevant results
                'suggestions': suggestions,
                'search_strategy': 'trusted_domains_only'
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
        """Calculate relevance score for a search result with better filtering"""
        score = base_score
        
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        content = f"{title} {snippet}"
        url = result.get('link', '').lower()
        
        # FILTER OUT completely irrelevant results
        irrelevant_patterns = [
            'privacy policy', 'terms of service', 'cookie policy', 'help center',
            'support documentation', 'user guide', 'tutorial', 'how to',
            'general compliance', 'product features', 'pricing', 'download',
            'sign up', 'log in', 'create account', 'software documentation'
        ]
        
        # Check if result is generic/irrelevant
        for pattern in irrelevant_patterns:
            if pattern in content and entity_name.lower() not in content:
                score *= 0.1  # Heavy penalty for irrelevant content
                break
        
        # Name matching - REQUIRE entity name presence for high relevance
        entity_name_lower = entity_name.lower()
        entity_name_parts = entity_name_lower.replace(',', '').replace('.', '').split()
        
        # Check for exact entity name match
        if entity_name_lower in content:
            score += 0.3
        else:
            # Check for individual name parts
            matching_parts = 0
            for part in entity_name_parts:
                if len(part) > 2 and part in content:
                    matching_parts += 1
                    score += 0.1
            
            # If no name parts match, heavily penalize
            if matching_parts == 0:
                score *= 0.2
        
        # CRITICAL: High-value enforcement/sanctions keywords
        critical_keywords = [
            'sanctions', 'sanctioned', 'wanted', 'fugitive', 'arrested',
            'indicted', 'charged', 'investigation', 'enforcement',
            'violated', 'penalty', 'fine', 'prosecution', 'criminal',
            'fraud', 'money laundering', 'terror', 'drug trafficking'
        ]
        
        critical_match = False
        for keyword in critical_keywords:
            if keyword in content:
                score += 0.25
                critical_match = True
        
        # Compliance and regulatory keywords (medium value)
        compliance_keywords = [
            'compliance', 'regulatory', 'violation', 'breach',
            'aml', 'kyc', 'cfpb', 'sec', 'finra', 'ofac', 'treasury',
            'financial crime', 'suspicious activity', 'due diligence'
        ]
        
        for keyword in compliance_keywords:
            if keyword in content:
                score += 0.15
        
        # OpenSanctions context matching - make it more specific
        if opensanctions_data and opensanctions_data.get('success'):
            os_results = opensanctions_data.get('data', {}).get('results', [])
            for os_result in os_results:
                countries = [c.lower() for c in os_result.get('countries', [])]
                datasets = [d.lower() for d in os_result.get('datasets', [])]
                
                # Country matching with context
                for country in countries:
                    if country in content and any(keyword in content for keyword in critical_keywords + compliance_keywords):
                        score += 0.3
                
                # Dataset-specific matching
                for dataset in datasets:
                    if 'wanted' in dataset and any(word in content for word in ['wanted', 'fugitive', 'arrest']):
                        score += 0.4
                    elif 'sanction' in dataset and any(word in content for word in ['sanction', 'penalty', 'enforcement']):
                        score += 0.4
        
        # Penalty for very short snippets or generic content
        if len(snippet) < 50:
            score *= 0.7
        
        # MINIMUM RELEVANCE THRESHOLD
        # If no critical keywords AND no entity name match, mark as irrelevant
        if not critical_match and entity_name_lower not in content:
            score *= 0.1
        
        return min(max(score, 0.0), 1.0)  # Cap between 0.0 and 1.0
    
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
            # Ensure total_results is a number
            if isinstance(total_results, (int, float)):
                total_results = int(total_results)
            else:
                total_results = 0
            
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
        """Check if URL is from a trusted domain - improved precision"""
        domain = self._extract_domain(url).lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check for exact domain match or subdomain match
        for trusted in self.trusted_domains:
            trusted_lower = trusted.lower()
            if domain == trusted_lower or domain.endswith('.' + trusted_lower):
                logger.info(f"Trusted domain found: {domain} matches {trusted_lower}")
                return True
        
        logger.info(f"Non-trusted domain filtered out: {domain}")
        return False
    
    def _get_source_name(self, domain: str) -> str:
        """Get human-readable source name from domain"""
        source_mapping = {
            # News Sources
            'bbc.com': 'BBC News',
            'reuters.com': 'Reuters',
            'apnews.com': 'Associated Press',
            'cnn.com': 'CNN',
            'theguardian.com': 'The Guardian',
            'wsj.com': 'The Wall Street Journal',
            'ft.com': 'Financial Times',
            'bloomberg.com': 'Bloomberg',
            'hindustantimes.com': 'Hindustan Times',
            'forbes.com': 'Forbes',
            
            # Government Sources
            'treasury.gov': 'U.S. Department of Treasury',
            'fincen.gov': 'Financial Crimes Enforcement Network',
            'sec.gov': 'Securities and Exchange Commission',
            'fbi.gov': 'Federal Bureau of Investigation',
            'justice.gov': 'U.S. Department of Justice',
            'state.gov': 'U.S. Department of State',
            'europa.eu': 'European Union',
            
            # Compliance and Legal
            'opensanctions.org': 'OpenSanctions',
            'sanctionslist.eu': 'EU Sanctions List',
            'ofac.treasury.gov': 'OFAC Sanctions List',
            'un.org': 'United Nations',
            
            # Financial Industry
            'swift.com': 'SWIFT',
            'fatf-gafi.org': 'Financial Action Task Force',
            'wolfsberg-principles.com': 'Wolfsberg Group'
        }
        
        # Check for exact domain match first
        if domain in source_mapping:
            return source_mapping[domain]
        
        # Check for partial domain matches
        for trusted_domain, source_name in source_mapping.items():
            if trusted_domain in domain:
                return source_name
        
        # Fallback to domain name
        return domain
    
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