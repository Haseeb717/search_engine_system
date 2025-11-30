"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.search.return_value = {
        'hits': {
            'total': {'value': 100},
            'hits': [
                {
                    '_id': '1',
                    '_score': 0.95,
                    '_source': {
                        'url': 'https://example.com/test',
                        'title': 'Test Page',
                        'content': 'This is test content',
                        'domain': 'example.com',
                        'crawl_date': '2024-11-29T12:00:00'
                    }
                }
            ]
        }
    }
    mock.index.return_value = {'result': 'created'}
    return mock


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL client."""
    mock = AsyncMock()
    mock.engine = MagicMock()
    mock.create_job.return_value = 'test-job-id'
    mock.get_job.return_value = {
        'id': 'test-job-id',
        'job_type': 'recrawl',
        'url': 'https://example.com',
        'status': 'pending',
        'priority': 10,
        'created_at': '2024-11-29T12:00:00',
        'sla_deadline': '2024-11-29T13:00:00'
    }
    mock.update_job_status.return_value = True
    return mock


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ client."""
    mock = MagicMock()
    mock.connection = MagicMock()
    mock.connection.is_closed = False
    mock.publish_recrawl_job.return_value = True
    mock.publish_crawl_job.return_value = True
    return mock


@pytest.fixture
def test_client(mock_redis, mock_elasticsearch, mock_postgres, mock_rabbitmq):
    """
    Test client with mocked dependencies.
    """
    with patch('app.db.redis_client.redis_client') as mock_redis_client, \
         patch('app.db.elasticsearch_client.es_client') as mock_es_client, \
         patch('app.db.postgres_client.postgres_client') as mock_pg_client, \
         patch('app.db.rabbitmq_client.rabbitmq_client') as mock_rmq_client, \
         patch('app.core.rate_limit.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit, \
         patch('app.core.auth.get_api_key', new_callable=AsyncMock) as mock_get_api_key:
        
        # Setup rate limit and auth mocks (no-op for tests)
        mock_rate_limit.return_value = None
        mock_get_api_key.return_value = {"name": "test-user", "rate_limit": 1000}
        
        # Setup Redis mock
        mock_redis_client.connect = AsyncMock()
        mock_redis_client.disconnect = AsyncMock()
        mock_redis_client.client = mock_redis
        # Mock the async methods directly on redis_client
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.set = AsyncMock(return_value=True)
        mock_redis_client.delete = AsyncMock(return_value=True)
        mock_redis_client.exists = AsyncMock(return_value=False)
        # Mock client.ttl for rate limiter
        mock_redis_client.client.ttl = AsyncMock(return_value=60)
        
        # Setup Elasticsearch mock
        mock_es_client.connect = AsyncMock()
        mock_es_client.disconnect = AsyncMock()
        mock_es_client.create_index = AsyncMock()
        mock_es_client.client = mock_elasticsearch
        mock_es_client.search = AsyncMock(return_value={
            'hits': {
                'total': {'value': 100},
                'hits': []
            }
        })
        
        # Setup PostgreSQL mock
        mock_pg_client.connect = AsyncMock()
        mock_pg_client.disconnect = AsyncMock()
        mock_pg_client.engine = MagicMock()
        mock_pg_client.create_job = AsyncMock(return_value='test-job-id')
        mock_pg_client.get_job = AsyncMock(return_value={
            'id': 'test-job-id',
            'job_type': 'recrawl',
            'url': 'https://example.com',
            'status': 'pending',
            'priority': 10,
            'created_at': '2024-11-29T12:00:00',
            'sla_deadline': '2024-11-29T13:00:00'
        })
        mock_pg_client.update_job_status = AsyncMock()
        
        # Setup RabbitMQ mock
        mock_rmq_client.connect = MagicMock()
        mock_rmq_client.disconnect = MagicMock()
        mock_rmq_client.connection = MagicMock()
        mock_rmq_client.connection.is_closed = False
        mock_rmq_client.publish_recrawl_job = MagicMock()
        
        from app.main import app
        client = TestClient(app)
        yield client


@pytest.fixture
def sample_search_request():
    """Sample search request."""
    return {
        "query": "python tutorial",
        "page": 1,
        "page_size": 10
    }


@pytest.fixture
def sample_recrawl_request():
    """Sample re-crawl request."""
    return {
        "url": "https://example.com/page",
        "priority": 10
    }