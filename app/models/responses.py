"""
Pydantic response models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class SearchResultItem(BaseModel):
    """Single search result item."""
    
    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    snippet: str = Field(..., description="Text snippet/preview")
    domain: str = Field(..., description="Domain name")
    crawl_date: Optional[str] = Field(None, description="Last crawl date")
    score: Optional[float] = Field(None, description="Relevance score")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    results: List[SearchResultItem] = Field(default=[], description="Search results")
    search_time_ms: float = Field(..., description="Search time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was cached")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "python tutorial",
                "total_results": 1250,
                "page": 1,
                "page_size": 10,
                "total_pages": 125,
                "results": [
                    {
                        "url": "https://example.com/python-tutorial",
                        "title": "Learn Python - Complete Tutorial",
                        "snippet": "A comprehensive guide to learning Python programming...",
                        "domain": "example.com",
                        "crawl_date": "2024-11-29T12:00:00",
                        "score": 0.95
                    }
                ],
                "search_time_ms": 45.2,
                "cached": False
            }
        }


class JobResponse(BaseModel):
    """Response model for job creation."""
    
    job_id: str = Field(..., description="Unique job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation time")
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline (for re-crawls)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Re-crawl job created successfully",
                "created_at": "2024-11-29T12:00:00",
                "sla_deadline": "2024-11-29T13:00:00"
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""
    
    job_id: str = Field(..., description="Job ID")
    job_type: str = Field(..., description="Type of job (crawl/recrawl)")
    url: str = Field(..., description="URL being crawled")
    status: str = Field(..., description="Current status")
    priority: int = Field(..., description="Job priority")
    created_at: Optional[datetime] = Field(None, description="Creation time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    "documents_indexed": 1,
                    "status_code": 200
                },
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "detail": "Query string must be at least 1 character"
            }
        }