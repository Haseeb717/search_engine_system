"""
Search service for handling search queries.
"""
import time
from typing import Dict, Any
from app.db.elasticsearch_client import es_client
from app.services.cache_service import cache_service
from app.models.responses import SearchResponse, SearchResultItem


class SearchService:
    """Service for executing search queries."""
    
    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10
    ) -> SearchResponse:
        """
        Execute a search query with caching.
        
        Args:
            query: Search query string
            page: Page number
            page_size: Results per page
            
        Returns:
            SearchResponse with results
        """
        start_time = time.time()
        
        # Check cache first
        cached_result = await cache_service.get_search_results(query, page, page_size)
        if cached_result:
            # Add timing and cache flag
            search_time = (time.time() - start_time) * 1000
            cached_result['search_time_ms'] = round(search_time, 2)
            cached_result['cached'] = True
            return SearchResponse(**cached_result)
        
        # Cache miss - query Elasticsearch
        from_offset = (page - 1) * page_size
        es_results = await es_client.search(
            query=query,
            size=page_size,
            from_=from_offset
        )
        
        # Parse Elasticsearch results
        results = self._parse_es_results(es_results)
        total_results = es_results['hits']['total']['value']
        total_pages = (total_results + page_size - 1) // page_size  # Ceiling division
        
        # Build response
        search_time = (time.time() - start_time) * 1000
        response_data = {
            'query': query,
            'total_results': total_results,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': results,
            'search_time_ms': round(search_time, 2),
            'cached': False
        }
        
        # Cache the results for next time
        await cache_service.set_search_results(query, page, page_size, response_data)
        
        return SearchResponse(**response_data)
    
    def _parse_es_results(self, es_response: Dict[str, Any]) -> list[SearchResultItem]:
        """
        Parse Elasticsearch response into SearchResultItem list.
        
        Args:
            es_response: Raw Elasticsearch response
            
        Returns:
            List of SearchResultItem objects
        """
        results = []
        
        for hit in es_response.get('hits', {}).get('hits', []):
            source = hit['_source']
            
            # Get highlighted snippet if available
            snippet = ""
            if 'highlight' in hit and 'content' in hit['highlight']:
                snippet = " ... ".join(hit['highlight']['content'])
            else:
                # Fallback to first 200 chars of content
                content = source.get('content', '')
                snippet = content[:200] + "..." if len(content) > 200 else content
            
            result_item = SearchResultItem(
                url=source.get('url', ''),
                title=source.get('title', 'No title'),
                snippet=snippet,
                domain=source.get('domain', ''),
                crawl_date=source.get('crawl_date'),
                score=hit.get('_score')
            )
            results.append(result_item)
        
        return results


# Global search service instance
search_service = SearchService()