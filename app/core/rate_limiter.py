"""
Rate limiting utilities for the AI Code Review Agent.

This module provides rate limiting functionality using slowapi
and Redis as the storage backend.
"""

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    # Create dummy classes for when slowapi is not available
    class Limiter:
        def __init__(self, *args, **kwargs):
            pass
        def limit(self, rate):
            def decorator(func):
                return func
            return decorator
    
    class RateLimitExceeded(Exception):
        def __init__(self, retry_after=60):
            self.retry_after = retry_after

try:
    from fastapi import Request, Response
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = None
    Response = None

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

# Initialize settings
settings = get_settings()

# Create Redis connection for rate limiting
redis_client = None
if REDIS_AVAILABLE:
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info("Rate limiter Redis connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
        # Fallback to in-memory storage (not recommended for production)
        redis_client = None


def get_client_identifier(request):
    """
    Get client identifier for rate limiting.
    
    Uses IP address as the primary identifier, with fallback options.
    In production, you might want to use API keys or user IDs.
    """
    if not FASTAPI_AVAILABLE or not request:
        return "unknown"
        
    # Try to get real IP from headers (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP if multiple are present
        client_ip = forwarded_for.split(',')[0].strip()
    else:
        if SLOWAPI_AVAILABLE:
            client_ip = get_remote_address(request)
        else:
            client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown'
    
    # For authenticated requests, you could use user ID instead
    # user_id = request.headers.get("X-User-ID")
    # if user_id:
    #     return f"user:{user_id}"
    
    return f"ip:{client_ip}"


# Initialize the limiter
if SLOWAPI_AVAILABLE:
    limiter = Limiter(
        key_func=get_client_identifier,
        storage_uri=settings.REDIS_URL if redis_client else "memory://",
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"]
    )
else:
    # Fallback limiter when slowapi is not available
    limiter = Limiter()


async def rate_limit_exceeded_handler(request, exc):
    """
    Custom rate limit exceeded handler.
    
    Returns a structured error response when rate limit is exceeded.
    """
    if not FASTAPI_AVAILABLE:
        return None
        
    client_id = get_client_identifier(request)
    
    logger.warning(
        "Rate limit exceeded",
        client_id=client_id,
        path=request.url.path if hasattr(request.url, 'path') else 'unknown',
        method=request.method if hasattr(request, 'method') else 'unknown',
        retry_after=getattr(exc, 'retry_after', 60)
    )
    
    retry_after = getattr(exc, 'retry_after', 60)
    
    if Response:
        response = Response(
            content=f'{{"error": "rate_limit_exceeded", "message": "Too many requests. Try again in {retry_after} seconds.", "retry_after": {retry_after}}}',
            status_code=429,
            headers={
                "Content-Type": "application/json",
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(retry_after)
            }
        )
        return response
    
    return None


# Rate limiting decorators for different endpoint types
def standard_rate_limit():
    """Standard rate limit for most endpoints."""
    if SLOWAPI_AVAILABLE:
        # Use the correct syntax for slowapi with FastAPI
        return limiter.limit(f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute")
    else:
        # Return a no-op decorator when slowapi is not available
        def decorator(func):
            return func
        return decorator


def analysis_rate_limit():
    """More restrictive rate limit for analysis endpoints."""
    if SLOWAPI_AVAILABLE:
        # Analysis endpoints are more resource-intensive
        analysis_limit = max(1, settings.RATE_LIMIT_REQUESTS_PER_MINUTE // 4)  # 1/4 of standard limit
        return limiter.limit(f"{analysis_limit}/minute")
    else:
        # Return a no-op decorator when slowapi is not available
        def decorator(func):
            return func
        return decorator


def status_rate_limit():
    """Higher rate limit for status checking endpoints."""
    if SLOWAPI_AVAILABLE:
        # Status endpoints are lightweight, allow more requests
        status_limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE * 2
        return limiter.limit(f"{status_limit}/minute")
    else:
        # Return a no-op decorator when slowapi is not available
        def decorator(func):
            return func
        return decorator


def webhook_rate_limit():
    """Rate limit for webhook endpoints."""
    if SLOWAPI_AVAILABLE:
        # Webhooks should have reasonable limits but not be too restrictive
        webhook_limit = max(10, settings.RATE_LIMIT_REQUESTS_PER_MINUTE // 2)
        return limiter.limit(f"{webhook_limit}/minute")
    else:
        # Return a no-op decorator when slowapi is not available
        def decorator(func):
            return func
        return decorator


# Dependency function for rate limiting
async def rate_limit_dependency(request):
    """Dependency function to be used with FastAPI Depends() for rate limiting."""
    # This function doesn't do anything, but ensures Request is available
    # The actual rate limiting is handled by the decorator
    return request
