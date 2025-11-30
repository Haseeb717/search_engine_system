"""
Crawl endpoint for requesting page re-crawls.
Includes authentication, rate limiting, and comprehensive error handling.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.requests import RecrawlRequest
from app.models.responses import JobResponse, ErrorResponse
from app.services.crawl_service import crawl_service
from app.core.auth import get_api_key
from app.core.rate_limit import check_rate_limit

router = APIRouter(
    prefix="/crawl",
    tags=["Crawl"]
)


@router.post(
    "/recrawl",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request re-crawl of a page",
    description="Submit a high-priority re-crawl request with 1-hour SLA",
    responses={
        202: {
            "description": "Re-crawl job accepted and queued",
            "model": JobResponse
        },
        400: {
            "description": "Invalid request parameters",
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
        },
        503: {
            "description": "Service unavailable (queue full)",
            "model": ErrorResponse
        }
    }
)
async def recrawl_page(
    request: RecrawlRequest,
    http_request: Request,
    api_key_data: dict = Depends(get_api_key)
) -> JobResponse:
    """
    Request re-crawl of a specific URL.
    
    **Authentication**: Requires X-API-Key header (optional for demo)
    **Rate Limit**: 1000 requests/minute per API key
    
    **Request Parameters:**
    - **url**: Valid HTTP/HTTPS URL to re-crawl
    - **priority**: Priority level 0-10 (default: 10 for re-crawls)
    
    **SLA**: Re-crawl will complete within 1 hour.
    
    **Response:**
    Returns a job ID that can be used to track progress via the /jobs/{job_id} endpoint.
    
    **Scaling Notes:**
    - Jobs are queued in RabbitMQ with priority
    - Dedicated worker pool ensures SLA compliance
    - Auto-scaling based on queue depth
    """
    try:
        # Check rate limit
        await check_rate_limit(http_request, api_key_data)
        
        # Validate URL format (additional to Pydantic validation)
        url_str = str(request.url)
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "Invalid URL format",
                    "detail": "URL must start with http:// or https://"
                }
            )
        
        # Check if URL is too long
        if len(url_str) > 2048:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "URL too long",
                    "detail": "URL must be less than 2048 characters"
                }
            )
        
        # Create re-crawl job through service layer
        job = await crawl_service.create_recrawl_job(
            url=request.url,
            priority=request.priority
        )
        
        return job
        
    except HTTPException:
        # Re-raise HTTP exceptions
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
        # Handle connection errors (database, queue)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Unable to queue crawl job",
                "detail": "Message queue or database temporarily unavailable"
            }
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Unexpected error in recrawl: {type(e).__name__}: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to create re-crawl job",
                "detail": "The error has been logged and will be investigated"
            }
        )