"""
FastAPI application entry point.
Main application with all routes, middleware, and lifecycle management.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import time

from app.core.config import settings
from app.db import redis_client, es_client, postgres_client, rabbitmq_client
from app.api.endpoints import search_router, crawl_router, jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Connect to all services
    print("🚀 Starting Search Engine API...")
    
    try:
        # Connect to Redis
        await redis_client.connect()
        
        # Connect to Elasticsearch
        await es_client.connect()
        await es_client.create_index()  # Create index if not exists
        
        # Connect to PostgreSQL
        await postgres_client.connect()
        
        # Connect to RabbitMQ
        rabbitmq_client.connect()
        
        print("✅ All services connected successfully")
        
    except Exception as e:
        print(f"❌ Error connecting to services: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown: Disconnect from all services
    print("🛑 Shutting down Search Engine API...")
    
    try:
        await redis_client.disconnect()
        await es_client.disconnect()
        await postgres_client.disconnect()
        rabbitmq_client.disconnect()
        
        print("✅ All services disconnected successfully")
        
    except Exception as e:
        print(f"❌ Error disconnecting from services: {e}")


# Create FastAPI application
app = FastAPI(
    title="Scalable Search Engine API",
    description="""
    A web-scale search engine API capable of:
    - Searching through billions of indexed web pages
    - Handling ~100 billion queries per month
    - Re-crawling pages on-demand with 1-hour SLA
    
    ## Features
    * **High Performance**: 80% cache hit rate for sub-50ms responses
    * **Scalability**: Horizontal scaling across all components
    * **Reliability**: Queue-based architecture with job tracking
    * **Security**: API key authentication and rate limiting
    
    ## Authentication
    Include your API key in the `X-API-Key` header (optional for demo)
    
    ## Rate Limiting
    Default: 1000 requests/minute per API key
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ========== MIDDLEWARE ==========

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware (for performance monitoring)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# ========== EXCEPTION HANDLERS ==========

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.
    Returns user-friendly error messages.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "detail": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    Logs error and returns generic error response.
    """
    print(f"Unhandled exception: {type(exc).__name__}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": "The error has been logged and will be investigated"
        }
    )


# ========== ROUTES ==========

# Include API routers
app.include_router(search_router, prefix="/api/v1")
app.include_router(crawl_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "service": "Search Engine API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "features": {
            "search": "POST /api/v1/search",
            "recrawl": "POST /api/v1/crawl/recrawl",
            "job_status": "GET /api/v1/jobs/{job_id}"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the status of all connected services.
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_client.client:
            await redis_client.client.ping()
            health_status["services"]["redis"] = "connected"
        else:
            health_status["services"]["redis"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["redis"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check Elasticsearch
    try:
        if es_client.client:
            await es_client.client.ping()
            health_status["services"]["elasticsearch"] = "connected"
        else:
            health_status["services"]["elasticsearch"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["elasticsearch"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        if postgres_client.engine:
            health_status["services"]["postgresql"] = "connected"
        else:
            health_status["services"]["postgresql"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["postgresql"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check RabbitMQ
    try:
        if rabbitmq_client.connection and not rabbitmq_client.connection.is_closed:
            health_status["services"]["rabbitmq"] = "connected"
        else:
            health_status["services"]["rabbitmq"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["rabbitmq"] = "disconnected"
        health_status["status"] = "degraded"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )