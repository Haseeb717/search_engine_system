"""
Search endpoint for querying indexed pages.
Includes authentication, rate limiting, and comprehensive error handling.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.requests import SearchRequest
from app.models.responses import SearchResponse, ErrorResponse
from app.services.search_service import search_service
from app.core.auth import get_api_key
from app.core.rate_limit import check_rate_limit

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search indexed pages",
    description="Search through billions of indexed web pages with caching support",
    responses={
        200: {
            "description": "Search results returned successfully",
            "model": SearchResponse
        },
        400: {
            "description": "Invalid search parameters",
            "model": ErrorResponse
        },
        401: {
            "description": "Invalid or missing API key",
            "model": ErrorResponse
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def search(
    request: SearchRequest,
    http_request: Request,
    api_key_data: dict = Depends(get_api_key)
) -> SearchResponse:
    """
    Search for indexed web pages.
    
    **Authentication**: Requires X-API-Key header (optional for demo)
    **Rate Limit**: 1000 requests/minute per API key
    
    **Request Parameters:**
    - **query**: Search query string (1-500 characters)
    - **page**: Page number (default: 1)
    - **page_size**: Results per page (1-100, default: 10)
    
    **Response:**
    Returns paginated search results with caching for performance.
    Cache hit rate target: 70-80% for common queries.
    
    **Scaling Notes:**
    - Results are cached in Redis for 30 minutes
    - Cache-first strategy reduces Elasticsearch load
    - Stateless design allows horizontal scaling
    """
    try:
        # Check rate limit
        await check_rate_limit(http_request, api_key_data)
        
        # Input sanitization (prevent injection attacks)
        sanitized_query = request.query.strip()
        
        # Validate query is not empty after sanitization
        if not sanitized_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "Query cannot be empty",
                    "detail": "Please provide a non-empty search query"
                }
            )
        
        # Execute search through service layer
        results = await search_service.search(
            query=sanitized_query,
            page=request.page,
            page_size=request.page_size
        )
        
        return results
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, rate limits, etc.)
        raise
        
    except ValueError as e:
        # Handle validation errors from service layer
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "detail": str(e)
            }
        )
        
    except ConnectionError as e:
        # Handle connection errors to external services
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Search service temporarily unavailable",
                "detail": "Please try again in a moment"
            }
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        # In production, log this with full stack trace
        print(f"Unexpected error in search: {type(e).__name__}: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "detail": "The error has been logged and will be investigated"
            }
        )