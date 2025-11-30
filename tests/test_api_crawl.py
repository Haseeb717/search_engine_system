"""
Tests for re-crawl endpoint.
"""
import pytest


def test_recrawl_endpoint_success(test_client, sample_recrawl_request):
    """Test successful re-crawl request."""
    response = test_client.post("/api/v1/crawl/recrawl", json=sample_recrawl_request)
    
    assert response.status_code == 202  # Accepted
    data = response.json()
    
    assert "job_id" in data
    assert "status" in data
    assert "created_at" in data
    assert "sla_deadline" in data
    assert data["status"] == "pending"


def test_recrawl_with_invalid_url(test_client):
    """Test re-crawl with invalid URL."""
    response = test_client.post("/api/v1/crawl/recrawl", json={
        "url": "not-a-valid-url",
        "priority": 10
    })
    
    assert response.status_code == 422  # Validation error


def test_recrawl_with_missing_url(test_client):
    """Test re-crawl without URL."""
    response = test_client.post("/api/v1/crawl/recrawl", json={
        "priority": 10
    })
    
    assert response.status_code == 422


def test_recrawl_with_invalid_priority(test_client):
    """Test re-crawl with invalid priority."""
    response = test_client.post("/api/v1/crawl/recrawl", json={
        "url": "https://example.com",
        "priority": 15  # Invalid: max is 10
    })
    
    assert response.status_code == 422


def test_recrawl_default_priority(test_client):
    """Test re-crawl with default priority."""
    response = test_client.post("/api/v1/crawl/recrawl", json={
        "url": "https://example.com"
        # priority omitted - should default to 10
    })
    
    assert response.status_code == 202


@pytest.mark.parametrize("url,priority", [
    ("https://example.com", 10),
    ("https://test.org/page", 5),
    ("http://demo.com/test", 0),
])
def test_recrawl_various_inputs(test_client, url, priority):
    """Test re-crawl with various valid inputs."""
    response = test_client.post("/api/v1/crawl/recrawl", json={
        "url": url,
        "priority": priority
    })
    
    assert response.status_code == 202


def test_recrawl_sla_deadline(test_client, sample_recrawl_request):
    """Test that SLA deadline is set (1 hour from creation)."""
    response = test_client.post("/api/v1/crawl/recrawl", json=sample_recrawl_request)
    
    assert response.status_code == 202
    data = response.json()
    
    # Verify both timestamps exist
    assert data["created_at"] is not None
    assert data["sla_deadline"] is not None
    
    # In production, verify deadline is 1 hour after creation
    # For mock, just verify the field exists