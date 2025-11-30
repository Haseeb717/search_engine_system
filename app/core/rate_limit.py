"""
Rate limiting middleware using token bucket algorithm.
Demonstrates how to implement rate limiting at scale.
"""
import time
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from app.db.redis_client import redis_client


class RateLimiter:
    """
    Token bucket rate limiter using Redis.
    Scales horizontally across multiple API instances.
    """
    
    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds
    
    async def check_rate_limit(
        self, 
        identifier: str,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (API key, IP, user ID)
            limit: Custom rate limit (overrides default)
            
        Returns:
            Dict with rate limit info
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        limit = limit or self.requests_per_minute
        
        # Redis key for this identifier
        key = f"rate_limit:{identifier}"
        
        # Get current count
        current = await redis_client.get(key)
        count = int(current) if current else 0
        
        # Check if limit exceeded
        if count >= limit:
            # Get TTL to know when limit resets
            ttl = await self._get_ttl(key)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit of {limit} requests per minute exceeded",
                    "detail": f"Try again in {ttl} seconds"
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + ttl),
                    "Retry-After": str(ttl)
                }
            )
        
        # Increment counter
        new_count = count + 1
        await redis_client.set(key, new_count, ttl=self.window_size)
        
        # Return rate limit info
        return {
            "limit": limit,
            "remaining": limit - new_count,
            "reset": int(time.time()) + self.window_size
        }
    
    async def _get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        if redis_client.client:
            ttl = await redis_client.client.ttl(key)
            return ttl if ttl > 0 else self.window_size
        return self.window_size


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=1000)


async def check_rate_limit(request: Request, api_key_data: dict) -> None:
    """
    Dependency function for FastAPI endpoints.
    
    Args:
        request: FastAPI request object
        api_key_data: API key metadata from auth
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use API key as identifier
    identifier = api_key_data.get("name", "anonymous")
    limit = api_key_data.get("rate_limit", 100)
    
    # Check rate limit
    rate_info = await rate_limiter.check_rate_limit(identifier, limit)
    
    # Add rate limit headers to response (would need middleware for this)
    # For now, just validate the limit
    return rate_info


# Example usage in endpoints:
# @router.post("/search")
# async def search(
#     request: Request,
#     api_key: dict = Depends(get_api_key),
#     rate_limit: dict = Depends(check_rate_limit)
# ):
#     pass