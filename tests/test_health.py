"""
Tests for health check endpoints.
"""


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "service" in data
    assert "status" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check_healthy(test_client):
    """Test health check when all services are healthy."""
    response = test_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "services" in data
    assert "redis" in data["services"]
    assert "elasticsearch" in data["services"]
    assert "postgresql" in data["services"]
    assert "rabbitmq" in data["services"]


def test_health_check_includes_timestamp(test_client):
    """Test that health check includes timestamp."""
    response = test_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))


def test_openapi_docs_available(test_client):
    """Test that OpenAPI documentation is accessible."""
    response = test_client.get("/docs")
    
    # Should redirect or return docs
    assert response.status_code in [200, 307]


def test_openapi_json_available(test_client):
    """Test that OpenAPI JSON schema is accessible."""
    response = test_client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data