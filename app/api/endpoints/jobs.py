"""
Jobs endpoint for checking crawl/re-crawl job status.
Includes authentication and comprehensive error handling.
"""
from fastapi import APIRouter, HTTPException, Path, status, Depends, Request
from app.models.responses import JobStatusResponse, ErrorResponse
from app.services.crawl_service import crawl_service
from app.core.auth import get_api_key
from app.core.rate_limit import check_rate_limit
import re

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


def validate_uuid(job_id: str) -> bool:
    """Validate UUID format."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(job_id))


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description="Retrieve the current status of a crawl or re-crawl job",
    responses={
        200: {
            "description": "Job status retrieved successfully",
            "model": JobStatusResponse
        },
        400: {
            "description": "Invalid job ID format",
            "model": ErrorResponse
        },
        401: {
            "description": "Invalid or missing API key",
            "model": ErrorResponse
        },
        404: {
            "description": "Job not found",
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
async def get_job_status(
    http_request: Request,
    job_id: str = Path(
        ...,
        description="Unique job ID (UUID format)",
        example="550e8400-e29b-41d4-a716-446655440000",
        min_length=36,
        max_length=36
    ),
    api_key_data: dict = Depends(get_api_key)
) -> JobStatusResponse:
    """
    Get detailed status of a crawl or re-crawl job.
    
    **Authentication**: Requires X-API-Key header (optional for demo)
    **Rate Limit**: 1000 requests/minute per API key
    
    **Path Parameters:**
    - **job_id**: UUID of the job (returned when job was created)
    
    **Possible statuses:**
    - `pending`: Job is queued, waiting to be processed
    - `processing`: Job is currently being executed
    - `completed`: Job finished successfully
    - `failed`: Job failed with errors
    
    **For re-crawl jobs**: Check `sla_deadline` to see when the 1-hour SLA expires.
    
    **Scaling Notes:**
    - Job status cached in Redis for fast retrieval
    - Database queries optimized with indexes
    - Read replicas used for high query load
    """
    try:
        # Check rate limit
        await check_rate_limit(http_request, api_key_data)
        
        # Validate job ID format
        if not validate_uuid(job_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "Invalid job ID format",
                    "detail": "Job ID must be a valid UUID"
                }
            )
        
        # Get job status from service layer
        job_status = await crawl_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "JobNotFound",
                    "message": f"Job with ID {job_id} not found",
                    "detail": "Please verify the job ID is correct"
                }
            )
        
        return job_status
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except ConnectionError:
        # Handle database connection errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Unable to retrieve job status",
                "detail": "Database temporarily unavailable"
            }
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Unexpected error in get_job_status: {type(e).__name__}: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve job status",
                "detail": "The error has been logged and will be investigated"
            }
        )