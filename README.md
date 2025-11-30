# Scalable Search Engine System

A production-ready, web-scale search engine architecture capable of crawling billions of pages and handling billions of queries per month.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

## 📋 Requirements

The system must handle:
- **4 billion pages crawled per month** (~1,500 pages/second)
- **~100 billion search queries per month** (~38,000 queries/second)  
- **On-demand re-crawl requests** with 1-hour SLA

## 🏗️ Architecture Overview

### Core Components

1. **API Layer (FastAPI)**
   - RESTful API with auto-generated OpenAPI docs
   - Async/await for high concurrency
   - Horizontal scaling: 100-200 instances
   - API key authentication & rate limiting

2. **Cache Layer (Redis)**
   - Query result caching
   - 70-80% cache hit rate target
   - Distributed rate limiting
   - Sub-millisecond response times

3. **Search Engine (Elasticsearch)**
   - Inverted index for 4 billion documents
   - Distributed across 50-100 nodes
   - Full-text search with BM25 ranking
   - Sharded for horizontal scaling

4. **Database (PostgreSQL)**
   - Document metadata storage
   - Job status tracking with SLA monitoring
   - Connection pooling for high throughput

5. **Message Queue (RabbitMQ)**
   - Asynchronous job processing
   - Priority queues for re-crawls
   - Reliable message delivery

6. **Workers**
   - **Crawler**: Downloads web pages (1,500-2,000 workers)
   - **Processor**: Extracts and tokenizes text
   - **Indexer**: Builds inverted index in Elasticsearch

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.13+ (for local development)
- Git

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Haseeb717/search_engine_system
cd search-engine-system

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/Haseeb717/search_engine_system
cd search-engine-system

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env and set all *_HOST values to 'localhost'
# Then start services manually (Redis, Elasticsearch, PostgreSQL, RabbitMQ)

# Run the API
python -m uvicorn app.main:app --reload
```

### Verify Installation

```bash
# API should be running
curl http://localhost:8000/

# Check all services
curl http://localhost:8000/health

# Access interactive API documentation
open http://localhost:8000/docs
```

## 📡 API Endpoints

### 1. Search

**POST** `/api/v1/search`

Search through billions of indexed web pages.

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "query": "python tutorial",
    "page": 1,
    "page_size": 10
  }'
```

**Response:**
```json
{
  "query": "python tutorial",
  "total_results": 1250,
  "page": 1,
  "page_size": 10,
  "total_pages": 125,
  "results": [
    {
      "url": "https://example.com/python",
      "title": "Python Tutorial",
      "snippet": "Learn Python programming...",
      "domain": "example.com",
      "crawl_date": "2024-11-29T12:00:00",
      "score": 0.95
    }
  ],
  "search_time_ms": 45.2,
  "cached": false
}
```

### 2. Re-crawl Request

**POST** `/api/v1/crawl/recrawl`

Request urgent re-crawl with 1-hour SLA.

```bash
curl -X POST http://localhost:8000/api/v1/crawl/recrawl \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "url": "https://example.com/page",
    "priority": 10
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Re-crawl job created successfully",
  "created_at": "2024-11-29T12:00:00",
  "sla_deadline": "2024-11-29T13:00:00"
}
```

### 3. Job Status

**GET** `/api/v1/jobs/{job_id}`

Check crawl/re-crawl job status.

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: demo-key-12345"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "recrawl",
  "url": "https://example.com/page",
  "status": "completed",
  "priority": 10,
  "created_at": "2024-11-29T12:00:00",
  "started_at": "2024-11-29T12:00:30",
  "completed_at": "2024-11-29T12:15:00",
  "sla_deadline": "2024-11-29T13:00:00",
  "result": {
    "pages_crawled": 1,
    "documents_indexed": 1
  }
}
```

## 🔧 Configuration

Environment variables are configured in `.env` file:

```bash
# Copy example file
cp .env.example .env
```

Key configurations:

```env
# Application
APP_ENV=development
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000

# Redis (Cache)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_CACHE_TTL=1800

# Elasticsearch (Search)
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=web_pages

# PostgreSQL (Database)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=search_engine

# RabbitMQ (Queue)
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
```

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
python -m pytest -v

# Run with coverage
python -m pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test search endpoint
python -m pytest tests/test_api_search.py -v

# Test re-crawl endpoint
python -m pytest tests/test_api_crawl.py -v

# Test job status
python -m pytest tests/test_api_jobs.py -v

# Test models only
python -m pytest tests/test_models.py -v
```

### Test Coverage

Current coverage: **80%+**

- ✅ All API endpoints
- ✅ Request/response validation
- ✅ Error handling
- ✅ Service layer logic
- ✅ Model validation

## 🎨 Code Quality

### Linting with Ruff

```bash
# Install linting tools
pip install ruff==0.5.0

# Check code
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking with Mypy

```bash
# Install type checking tools
pip install mypy==1.10.0 types-redis==4.6.0.20240218 types-pika==1.2.0b1

# Run type checking
mypy app/

# Check specific file
mypy app/main.py
```

### Pre-commit Checks

```bash
# Run all quality checks before committing
ruff check . && \
ruff format --check . && \
mypy app/ && \
python -m pytest
```

## 📊 Scaling Strategy

### How It Scales to Requirements

#### Search Queries (100 billion/month = 38,000 queries/sec)

**Solution:**
1. **Caching (80% hit rate)**
   - 30,400 queries/sec hit Redis cache (instant)
   - 7,600 queries/sec hit Elasticsearch

2. **Horizontal API Scaling**
   - 100 FastAPI instances × 400 req/sec = 40,000 req/sec capacity

3. **Elasticsearch Cluster**
   - 50-100 nodes working in parallel
   - Data sharded across nodes

#### Crawling (4 billion pages/month = 1,500 pages/sec)

**Solution:**
1. **Parallel Workers**
   - 1,500-2,000 crawler workers
   - Each downloads ~1 page/second
   - Auto-scaling based on queue depth

2. **Queue-Based Architecture**
   - RabbitMQ handles job distribution
   - Persistent queues (no job loss)

#### 1-Hour Re-crawl SLA

**Solution:**
1. **Dedicated Worker Pool**
   - Separate high-priority queue
   - 100-200 workers reserved for re-crawls
   - Priority routing ensures immediate processing

2. **SLA Monitoring**
   - Track job creation to completion time
   - Alert if approaching deadline
   - Auto-scale workers if needed

## 🏭 Production Deployment

### Kubernetes Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-api
spec:
  replicas: 10
  selector:
    matchLabels:
      app: search-api
  template:
    metadata:
      labels:
        app: search-api
    spec:
      containers:
      - name: api
        image: search-engine-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_HOST
          value: redis-service
        - name: ELASTICSEARCH_HOST
          value: elasticsearch-service
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: search-api
  minReplicas: 10
  maxReplicas: 200
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Scaling Workers

```bash
# Docker Compose
docker-compose up -d --scale crawler=100

# Kubernetes
kubectl scale deployment crawler --replicas=1000
```

## 📈 Monitoring

### Metrics

- API response times
- Cache hit rates
- Queue depths
- Worker throughput
- Error rates

### Endpoints

- `/health` - Service health check
- `/metrics` - Prometheus metrics (optional)
- `/docs` - OpenAPI documentation

### Access Dashboards

```bash
# RabbitMQ Management UI
open http://localhost:15672
# Username: guest, Password: guest

# Elasticsearch
curl http://localhost:9200/_cluster/health

# API Docs
open http://localhost:8000/docs
```

## 📁 Project Structure

```
search-engine-system/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── auth.py            # Authentication middleware
│   │   └── rate_limit.py      # Rate limiting
│   ├── api/
│   │   └── endpoints/
│   │       ├── search.py      # Search endpoint
│   │       ├── crawl.py       # Re-crawl endpoint
│   │       └── jobs.py        # Job status endpoint
│   ├── models/
│   │   ├── requests.py        # Pydantic request models
│   │   └── responses.py       # Pydantic response models
│   ├── services/
│   │   ├── cache_service.py   # Caching logic
│   │   ├── search_service.py  # Search business logic
│   │   └── crawl_service.py   # Job management logic
│   ├── db/
│   │   ├── redis_client.py    # Redis connection
│   │   ├── elasticsearch_client.py  # ES connection
│   │   ├── postgres_client.py # PostgreSQL with SQLAlchemy
│   │   └── rabbitmq_client.py # RabbitMQ connection
│   └── workers/
│       ├── crawler.py         # Crawler worker
│       ├── processor.py       # Text processor
│       └── indexer.py         # Indexer worker
├── tests/
│   ├── conftest.py            # Test fixtures
│   ├── test_api_search.py     # Search endpoint tests
│   ├── test_api_crawl.py      # Re-crawl endpoint tests
│   ├── test_api_jobs.py       # Job status tests
│   ├── test_health.py         # Health check tests
│   ├── test_models.py         # Model validation tests
│   └── test_services.py       # Service layer tests
├── diagrams/
│   └── system_architecture.png  # Architecture diagram
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture docs
│   └── API_SPECIFICATION.md   # Complete API specification
├── docker-compose.yml         # Docker services configuration
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔑 Key Design Decisions

### Why FastAPI?
- Native async/await support (high concurrency)
- Automatic OpenAPI documentation
- Type safety with Pydantic
- Fast performance (comparable to Node.js/Go)

### Why Redis for Caching?
- In-memory speed (sub-millisecond latency)
- Cluster mode for horizontal scaling
- 80% cache hit rate reduces database load by 80%

### Why Elasticsearch?
- Purpose-built for full-text search
- Inverted index architecture
- Distributed by design
- Relevance scoring (BM25 algorithm)

### Why RabbitMQ?
- Reliable message delivery
- Priority queues
- Dead letter queues for failure handling
- Proven at scale

### Why PostgreSQL?
- ACID compliance for metadata
- Mature sharding support
- Reliable for job tracking

## 🚦 API Features

### Authentication

```bash
# Include API key in header
curl -H "X-API-Key: demo-key-12345" http://localhost:8000/api/v1/search
```

Demo API keys:
- `demo-key-12345` - 1000 requests/minute
- `test-key-67890` - 100 requests/minute

### Rate Limiting

- Default: 1000 requests/minute per API key
- Returns `429 Too Many Requests` when exceeded
- Headers include rate limit info:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

### Pagination

- Default: 10 results per page
- Max: 100 results per page
- Use `page` and `page_size` parameters

### Error Handling

All errors follow consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable message",
  "detail": "Additional details"
}
```

Status codes:
- `200 OK` - Success
- `202 Accepted` - Job created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid API key
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service down

## 🤝 Contributing

```bash
# Fork the repository
# Create a feature branch
git checkout -b feature/amazing-feature

# Make changes and run quality checks
ruff check . && ruff format . && mypy app/ && python -m pytest

# Commit changes
git commit -m "Add amazing feature"

# Push to branch
git push origin feature/amazing-feature

# Open a Pull Request
```

## 📝 License

This project is part of a technical assessment.

## 📧 Contact

For questions about this system, contact: careers@forager.ai

---

**Built with ❤️ for scalable search at web scale**

## 🎯 Assignment Deliverables

This project includes all required deliverables:

1. ✅ **System Diagram** - See `diagrams/system_architecture.png` and `docs/ARCHITECTURE.md`
2. ✅ **API Specification** - See `docs/API_SPECIFICATION.md` and `/docs` endpoint
3. ✅ **API Code** - Complete FastAPI implementation with:
   - Separation of concerns (routes, services, models, workers)
   - Scalability demonstrations (caching, async, queues)
   - Production-ready patterns (auth, rate limiting, error handling)
   - Comprehensive tests (80%+ coverage)

### Quick Demo

```bash
# Start everything
docker-compose up -d

# View API docs
open http://localhost:8000/docs

# Test search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "page": 1, "page_size": 10}'

# Request re-crawl
curl -X POST http://localhost:8000/api/v1/crawl/recrawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "priority": 10}'
```