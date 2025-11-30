"""
API endpoints package.
"""
from app.api.endpoints.search import router as search_router
from app.api.endpoints.crawl import router as crawl_router
from app.api.endpoints.jobs import router as jobs_router

__all__ = [
    "search_router",
    "crawl_router",
    "jobs_router"
]