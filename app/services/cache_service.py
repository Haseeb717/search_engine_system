"""
Cache service for managing search result caching.
"""
from typing import Optional, Dict, Any
from app.db.redis_client import redis_client
import hashlib


class CacheService:
    """Service for caching search results and other data."""
    
    @staticmethod
    def _generate_cache_key(prefix: str, identifier: str) -> str:
        """
        Generate a cache key with prefix.
        
        Args:
            prefix: Key prefix (e.g., 'search', 'job')
            identifier: Unique identifier
            
        Returns:
            Cache key string
        """
        # Hash long identifiers to keep keys manageable
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"{prefix}:{identifier}"
    
    @staticmethod
    def _generate_search_key(query: str, page: int, page_size: int) -> str:
        """Generate cache key for search query."""
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        identifier = f"{normalized_query}:p{page}:s{page_size}"
        return CacheService._generate_cache_key("search", identifier)
    
    async def get_search_results(
        self, 
        query: str, 
        page: int, 
        page_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached search results.
        
        Args:
            query: Search query
            page: Page number
            page_size: Results per page
            
        Returns:
            Cached search results or None
        """
        cache_key = self._generate_search_key(query, page, page_size)
        return await redis_client.get(cache_key)
    
    async def set_search_results(
        self,
        query: str,
        page: int,
        page_size: int,
        results: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results.
        
        Args:
            query: Search query
            page: Page number
            page_size: Results per page
            results: Search results to cache
            ttl: Time to live (uses default if None)
            
        Returns:
            True if successful
        """
        cache_key = self._generate_search_key(query, page, page_size)
        return await redis_client.set(cache_key, results, ttl)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get cached job status."""
        cache_key = self._generate_cache_key("job", job_id)
        return await redis_client.get(cache_key)
    
    async def set_job_status(
        self,
        job_id: str,
        status_data: Dict[str, Any],
        ttl: int = 3600  # 1 hour default for job status
    ) -> bool:
        """Cache job status."""
        cache_key = self._generate_cache_key("job", job_id)
        return await redis_client.set(cache_key, status_data, ttl)
    
    async def invalidate_search_cache(self, query: str) -> int:
        """
        Invalidate all cached results for a query.
        
        Args:
            query: Search query
            
        Returns:
            Number of keys deleted
        """
        normalized_query = query.lower().strip()
        pattern = f"search:{normalized_query}:*"
        return await redis_client.clear_pattern(pattern)
    
    async def clear_all_search_cache(self) -> int:
        """Clear all search caches."""
        return await redis_client.clear_pattern("search:*")


# Global cache service instance
cache_service = CacheService()