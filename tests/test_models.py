"""
Tests for Pydantic models.
"""
import pytest
from pydantic import ValidationError
from app.models.requests import SearchRequest, RecrawlRequest
from app.models.responses import SearchResponse, JobResponse


def test_search_request_valid():
    """Test valid search request."""
    request = SearchRequest(
        query="python tutorial",
        page=1,
        page_size=10
    )
    
    assert request.query == "python tutorial"
    assert request.page == 1
    assert request.page_size == 10


def test_search_request_defaults():
    """Test search request with default values."""
    request = SearchRequest(query="test")
    
    assert request.page == 1
    assert request.page_size == 10


def test_search_request_invalid_page():
    """Test search request with invalid page."""
    with pytest.raises(ValidationError):
        SearchRequest(query="test", page=0)


def test_search_request_invalid_page_size():
    """Test search request with invalid page size."""
    with pytest.raises(ValidationError):
        SearchRequest(query="test", page_size=150)


def test_search_request_empty_query():
    """Test search request with empty query."""
    with pytest.raises(ValidationError):
        SearchRequest(query="")


def test_recrawl_request_valid():
    """Test valid re-crawl request."""
    request = RecrawlRequest(
        url="https://example.com",
        priority=10
    )
    
    assert str(request.url) == "https://example.com/"
    assert request.priority == 10


def test_recrawl_request_invalid_url():
    """Test re-crawl request with invalid URL."""
    with pytest.raises(ValidationError):
        RecrawlRequest(url="not-a-url", priority=10)


def test_recrawl_request_invalid_priority():
    """Test re-crawl request with invalid priority."""
    with pytest.raises(ValidationError):
        RecrawlRequest(url="https://example.com", priority=15)


def test_recrawl_request_default_priority():
    """Test re-crawl request with default priority."""
    request = RecrawlRequest(url="https://example.com")
    
    assert request.priority == 10


def test_search_response_model():
    """Test search response model."""
    response = SearchResponse(
        query="test",
        total_results=100,
        page=1,
        page_size=10,
        total_pages=10,
        results=[],
        search_time_ms=45.2,
        cached=False
    )
    
    assert response.query == "test"
    assert response.total_results == 100
    assert response.cached is False


def test_job_response_model():
    """Test job response model."""
    from datetime import datetime
    
    response = JobResponse(
        job_id="test-id",
        status="pending",
        message="Job created",
        created_at=datetime.now(),
        sla_deadline=None
    )
    
    assert response.job_id == "test-id"
    assert response.status == "pending"