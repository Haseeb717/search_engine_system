"""
Tests for search endpoint.
"""
import pytest
from unittest.mock import patch, AsyncMock


def test_search_endpoint_success(test_client, sample_search_request):
    """Test successful search request."""
    response = test_client.post("/api/v1/search", json=sample_search_request)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "query" in data
    assert "results" in data
    assert "total_results" in data
    assert "page" in data
    assert "page_size" in data
    assert data["query"] == "python tutorial"


def test_search_with_invalid_query(test_client):
    """Test search with empty query."""
    response = test_client.post("/api/v1/search", json={
        "query": "",
        "page": 1,
        "page_size": 10
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "ValidationError"


def test_search_with_invalid_page(test_client):
    """Test search with invalid page number."""
    response = test_client.post("/api/v1/search", json={
        "query": "test",
        "page": 0,  # Invalid: must be >= 1
        "page_size": 10
    })
    
    assert response.status_code == 400


def test_search_with_large_page_size(test_client):
    """Test search with page size exceeding limit."""
    response = test_client.post("/api/v1/search", json={
        "query": "test",
        "page": 1,
        "page_size": 150  # Invalid: max is 100
    })
    
    assert response.status_code == 400


def test_search_pagination(test_client):
    """Test search pagination."""
    # Page 1
    response1 = test_client.post("/api/v1/search", json={
        "query": "python",
        "page": 1,
        "page_size": 10
    })
    assert response1.status_code == 200
    
    # Page 2
    response2 = test_client.post("/api/v1/search", json={
        "query": "python",
        "page": 2,
        "page_size": 10
    })
    assert response2.status_code == 200


def test_search_caching(test_client, sample_search_request, mock_redis):
    """Test that search results are cached."""
    # First request - cache miss
    response1 = test_client.post("/api/v1/search", json=sample_search_request)
    assert response1.status_code == 200
    
    # Verify cache was checked
    mock_redis.get.assert_called()


def test_search_with_special_characters(test_client):
    """Test search with special characters in query."""
    response = test_client.post("/api/v1/search", json={
        "query": "python & java",
        "page": 1,
        "page_size": 10
    })
    
    assert response.status_code == 200


@pytest.mark.parametrize("query,page,page_size", [
    ("test", 1, 10),
    ("python programming", 1, 20),
    ("web development", 2, 50),
])
def test_search_various_inputs(test_client, query, page, page_size):
    """Test search with various valid inputs."""
    response = test_client.post("/api/v1/search", json={
        "query": query,
        "page": page,
        "page_size": page_size
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert data["page"] == page
    assert data["page_size"] == page_size