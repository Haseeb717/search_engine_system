"""
Tests for service layer.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_cache_service_generate_search_key():
    """Test cache key generation."""
    from app.services.cache_service import CacheService
    cache_service = CacheService()
    
    key1 = cache_service._generate_search_key("python", 1, 10)
    key2 = cache_service._generate_search_key("Python", 1, 10)  # Case insensitive
    
    # Should normalize to same key
    assert key1 == key2
    assert key1.startswith("search:")


@pytest.mark.asyncio
async def test_cache_service_set_and_get():
    """Test caching and retrieval."""
    from app.services.cache_service import CacheService
    cache_service = CacheService()
    
    with patch('app.db.redis_client.redis_client.get', new_callable=AsyncMock) as mock_get, \
         patch('app.db.redis_client.redis_client.set', new_callable=AsyncMock) as mock_set:
        
        mock_get.return_value = '{"test": "data"}'
        mock_set.return_value = True
        
        # Set cache
        result = await cache_service.set_search_results(
            "test query", 1, 10, {"test": "data"}
        )
        assert mock_set.called
        
        # Get cache
        cached = await cache_service.get_search_results("test query", 1, 10)
        assert mock_get.called


@pytest.mark.asyncio
async def test_search_service_parse_results():
    """Test Elasticsearch result parsing."""
    from app.services.search_service import SearchService
    search_service = SearchService()
    
    es_response = {
        'hits': {
            'total': {'value': 1},
            'hits': [
                {
                    '_id': '1',
                    '_score': 0.95,
                    '_source': {
                        'url': 'https://test.com',
                        'title': 'Test',
                        'content': 'Test content',
                        'domain': 'test.com',
                        'crawl_date': '2024-11-29'
                    }
                }
            ]
        }
    }
    
    results = search_service._parse_es_results(es_response)
    
    assert len(results) == 1
    assert results[0].url == 'https://test.com'
    assert results[0].title == 'Test'
    assert results[0].score == 0.95


@pytest.mark.asyncio
async def test_search_service_pagination_calculation():
    """Test pagination calculation."""
    from app.services.search_service import SearchService
    search_service = SearchService()
    
    with patch('app.db.elasticsearch_client.es_client.search', new_callable=AsyncMock) as mock_search, \
         patch('app.services.cache_service.cache_service.get_search_results', new_callable=AsyncMock) as mock_cache_get, \
         patch('app.services.cache_service.cache_service.set_search_results', new_callable=AsyncMock) as mock_cache_set:
        
        mock_search.return_value = {
            'hits': {
                'total': {'value': 250},
                'hits': []
            }
        }
        mock_cache_get.return_value = None
        mock_cache_set.return_value = True
        
        response = await search_service.search("test", page=1, page_size=10)
        
        # 250 results / 10 per page = 25 pages
        assert response.total_pages == 25
        assert response.total_results == 250