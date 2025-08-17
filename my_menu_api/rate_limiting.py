"""
Rate limiting middleware using Redis with Token Bucket algorithm.
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        redis_url: str = "redis://localhost:6379"
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.redis_url = redis_url


class TokenBucketRateLimiter:
    """Token Bucket rate limiter implementation using Redis."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
    
    async def init(self):
        """Initialize Redis connection for rate limiting."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Rate limiter Redis initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize rate limiter Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def is_allowed(
        self, 
        identifier: str, 
        endpoint: str = "default",
        custom_limit: Optional[int] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed using Token Bucket algorithm.
        
        Args:
            identifier: Client identifier (IP, user_id, etc.)
            endpoint: Endpoint being accessed
            custom_limit: Custom limit for specific endpoints
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        if not self.redis_client:
            # If Redis is down, allow requests (fail open)
            logger.warning("⚠️ Redis not available, allowing request")
            return True, {}
        
        current_time = time.time()
        
        # Different limits for different time windows
        limits = [
            ("minute", 60, custom_limit or self.config.requests_per_minute),
            ("hour", 3600, self.config.requests_per_hour)
        ]
        
        rate_limit_info = {}
        
        for window_name, window_seconds, max_requests in limits:
            key = f"rate_limit:{identifier}:{endpoint}:{window_name}"
            
            try:
                # Use Redis pipeline for atomic operations
                async with self.redis_client.pipeline() as pipe:
                    pipe.multi()
                    
                    # Get current bucket state
                    bucket_data = await self.redis_client.get(key)
                    
                    if bucket_data:
                        bucket = json.loads(bucket_data)
                        last_refill = bucket.get("last_refill", current_time)
                        tokens = bucket.get("tokens", max_requests)
                    else:
                        last_refill = current_time
                        tokens = max_requests
                    
                    # Calculate tokens to add based on time elapsed
                    time_elapsed = current_time - last_refill
                    tokens_to_add = time_elapsed * (max_requests / window_seconds)
                    new_tokens = min(max_requests, tokens + tokens_to_add)
                    
                    # Check if request can be served
                    if new_tokens >= 1:
                        new_tokens -= 1
                        allowed = True
                    else:
                        allowed = False
                    
                    # Update bucket state
                    bucket_state = {
                        "tokens": new_tokens,
                        "last_refill": current_time,
                        "requests_made": bucket.get("requests_made", 0) + (1 if allowed else 0)
                    }
                    
                    # Store updated state with expiration
                    pipe.setex(key, window_seconds * 2, json.dumps(bucket_state))
                    await pipe.execute()
                    
                    # Update rate limit info
                    rate_limit_info[f"{window_name}_remaining"] = int(new_tokens)
                    rate_limit_info[f"{window_name}_limit"] = max_requests
                    rate_limit_info[f"{window_name}_reset"] = int(current_time + window_seconds)
                    
                    if not allowed:
                        rate_limit_info["retry_after"] = int((1 - new_tokens) * (window_seconds / max_requests))
                        return False, rate_limit_info
            
            except Exception as e:
                logger.error(f"❌ Rate limiting error for {key}: {e}")
                # Fail open - allow request if Redis error
                return True, {}
        
        return True, rate_limit_info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, config: RateLimitConfig):
        super().__init__(app)
        self.rate_limiter = TokenBucketRateLimiter(config)
        self.config = config
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/auth/login": 5,  # 5 login attempts per minute
            "/auth/register": 3,  # 3 registrations per minute
            "/images/upload": 10,  # 10 uploads per minute
        }
        
        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", 
            "/healthz", "/readiness", "/liveness", "/metrics"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        start_time = time.time()
        
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            response = await call_next(request)
            return response
        
        # Get client identifier
        client_ip = self.get_client_ip(request)
        user_id = self.get_user_id(request)
        identifier = user_id if user_id else client_ip
        
        # Check custom endpoint limits
        endpoint = request.url.path
        custom_limit = self.endpoint_limits.get(endpoint)
        
        # Check rate limit
        try:
            allowed, rate_info = await self.rate_limiter.is_allowed(
                identifier, endpoint, custom_limit
            )
            
            if not allowed:
                # Return rate limit exceeded response
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": rate_info.get("retry_after", 60)
                    },
                    headers={
                        "Retry-After": str(rate_info.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(rate_info.get("minute_limit", self.config.requests_per_minute)),
                        "X-RateLimit-Remaining": str(rate_info.get("minute_remaining", 0)),
                        "X-RateLimit-Reset": str(rate_info.get("minute_reset", int(time.time()) + 60))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            if rate_info:
                response.headers["X-RateLimit-Limit"] = str(rate_info.get("minute_limit", self.config.requests_per_minute))
                response.headers["X-RateLimit-Remaining"] = str(rate_info.get("minute_remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(rate_info.get("minute_reset", int(time.time()) + 60))
            
            # Log rate limiting metrics
            process_time = time.time() - start_time
            logger.info(
                f"Rate limit check",
                extra={
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "allowed": allowed,
                    "remaining": rate_info.get("minute_remaining", 0),
                    "process_time": process_time
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Rate limiting middleware error: {e}")
            # Fail open - continue with request
            response = await call_next(request)
            return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated."""
        # This would be implemented based on your auth system
        # For example, you might decode JWT token here
        try:
            # Check if user is in request state (set by auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                return str(request.state.user.id)
        except Exception:
            pass
        return None


# Initialize rate limiter
async def init_rate_limiter(rate_limiter: TokenBucketRateLimiter):
    """Initialize rate limiter."""
    await rate_limiter.init()


async def close_rate_limiter(rate_limiter: TokenBucketRateLimiter):
    """Close rate limiter."""
    await rate_limiter.close()


# Helper function to create rate limit middleware
def create_rate_limit_middleware(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    burst_size: int = 10,
    redis_url: str = "redis://localhost:6379"
) -> RateLimitMiddleware:
    """Create and configure rate limit middleware."""
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        burst_size=burst_size,
        redis_url=redis_url
    )
    return RateLimitMiddleware(None, config)  # app will be set by FastAPI
