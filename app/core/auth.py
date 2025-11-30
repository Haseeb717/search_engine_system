"""
Authentication middleware for API key validation.
This is a demonstration implementation.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional

# Mock API keys (in production, store in database)
VALID_API_KEYS = {
    "demo-key-12345": {"name": "Demo User", "rate_limit": 1000},
    "test-key-67890": {"name": "Test User", "rate_limit": 100}
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> dict:
    """
    Validate API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key metadata
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # For demo purposes, allow requests without API key
    # In production, remove this and make API key required
    if not api_key:
        # Return default user for demo
        return {"name": "Anonymous", "rate_limit": 10}
    
    # Validate API key
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "InvalidAPIKey",
                "message": "Invalid or missing API key",
                "detail": "Please provide a valid API key in X-API-Key header"
            }
        )
    
    return VALID_API_KEYS[api_key]


# Example usage in endpoints:
# @router.post("/search", dependencies=[Depends(get_api_key)])
# async def search(api_key_data: dict = Depends(get_api_key)):
#     # api_key_data contains user info and rate limits
#     pass