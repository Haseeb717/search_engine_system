"""
Pydantic request models for API endpoints.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    
    query: str = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="Search query string"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination"
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results per page"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "python tutorial",
                "page": 1,
                "page_size": 10
            }
        }


class RecrawlRequest(BaseModel):
    """Request model for re-crawl endpoint."""
    
    url: HttpUrl = Field(
        ...,
        description="URL to re-crawl"
    )
    priority: int = Field(
        default=10,
        ge=0,
        le=10,
        description="Priority level (0-10, higher = more urgent)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/page",
                "priority": 10
            }
        }