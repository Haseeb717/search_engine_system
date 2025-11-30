"""
Tests for job status endpoint.
"""
import pytest
from unittest.mock import patch, AsyncMock


def test_get_job_status_success(test_client):
    """Test getting job status successfully."""
    job_id = "550e8400-e29b-41d4-a716-446655440000"
    response = test_client.get(f"/api/v1/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    assert "status" in data
    assert "url" in data
    assert "job_type" in data


def test_get_job_status_not_found(test_client):
    """Test getting non-existent job."""
    # Mock returning None for non-existent job
    with patch('app.db.postgres_client.postgres_client.get_job', new_callable=AsyncMock) as mock_get_job:
        mock_get_job.return_value = None
        
        job_id = "00000000-0000-0000-0000-000000000000"
        response = test_client.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "JobNotFound"


def test_get_job_status_invalid_uuid(test_client):
    """Test getting job with invalid UUID format."""
    response = test_client.get("/api/v1/jobs/not-a-uuid")
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "ValidationError"


def test_get_job_status_different_states(test_client):
    """Test getting jobs in different states."""
    states = ["pending", "processing", "completed", "failed"]
    
    for state in states:
        with patch('app.db.postgres_client.postgres_client.get_job', new_callable=AsyncMock) as mock_get_job:
            mock_get_job.return_value = {
                'id': 'test-job-id',
                'status': state,
                'job_type': 'recrawl',
                'url': 'https://example.com',
                'priority': 10,
                'created_at': '2024-11-29T12:00:00'
            }
            
            job_id = "550e8400-e29b-41d4-a716-446655440000"
            response = test_client.get(f"/api/v1/jobs/{job_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == state


def test_job_status_includes_all_fields(test_client):
    """Test that job status response includes all required fields."""
    job_id = "550e8400-e29b-41d4-a716-446655440000"
    response = test_client.get(f"/api/v1/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Required fields
    required_fields = [
        "job_id", "job_type", "url", "status", 
        "priority", "created_at"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"