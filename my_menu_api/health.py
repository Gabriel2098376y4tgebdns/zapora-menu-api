"""
Health check endpoints for application monitoring.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import get_db
from .cache import get_cache, RedisCache
from .logging_config import structured_logger

router = APIRouter(tags=["Health Checks"])


class HealthChecker:
    """Health check utility class."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_database_check = 0
        self.last_redis_check = 0
        self.check_cache_duration = 30  # Cache health check results for 30 seconds
    
    async def check_database(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and health."""
        current_time = time.time()
        
        try:
            start = time.time()
            
            # Simple connectivity test
            result = db.execute(text("SELECT 1"))
            connectivity_time = time.time() - start
            
            # Check if we can fetch the result
            result.fetchone()
            
            # Additional database health checks
            start = time.time()
            
            # Check if main tables exist
            table_checks = []
            tables_to_check = ["users", "menu_items", "audit_logs"]
            
            for table in tables_to_check:
                try:
                    db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    table_checks.append({"table": table, "status": "ok"})
                except Exception as e:
                    table_checks.append({"table": table, "status": "error", "error": str(e)})
            
            query_time = time.time() - start
            
            # Get connection pool info (if available)
            pool_info = {}
            if hasattr(db.bind, 'pool'):
                pool = db.bind.pool
                pool_info = {
                    "size": getattr(pool, 'size', None),
                    "checked_in": getattr(pool, 'checkedin', None),
                    "checked_out": getattr(pool, 'checkedout', None),
                    "overflow": getattr(pool, 'overflow', None),
                }
            
            return {
                "status": "healthy",
                "connectivity_time": round(connectivity_time, 4),
                "query_time": round(query_time, 4),
                "tables": table_checks,
                "pool_info": pool_info,
                "timestamp": current_time
            }
            
        except Exception as e:
            structured_logger.error(
                "Database health check failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_time
            }
    
    async def check_redis(self, cache: RedisCache) -> Dict[str, Any]:
        """Check Redis connectivity and health."""
        current_time = time.time()
        
        if not cache.is_connected:
            return {
                "status": "disconnected",
                "error": "Redis client not connected",
                "timestamp": current_time
            }
        
        try:
            start = time.time()
            
            # Test basic connectivity
            await cache.redis_client.ping()
            ping_time = time.time() - start
            
            # Test set/get operations
            start = time.time()
            test_key = "health_check_test"
            test_value = f"test_{current_time}"
            
            await cache.set(test_key, test_value, ttl=60)
            retrieved_value = await cache.get(test_key)
            await cache.delete(test_key)
            
            operation_time = time.time() - start
            
            # Verify the test worked
            if retrieved_value != test_value:
                raise Exception("Redis set/get test failed")
            
            # Get Redis info
            info = await cache.redis_client.info()
            
            return {
                "status": "healthy",
                "ping_time": round(ping_time, 4),
                "operation_time": round(operation_time, 4),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0),
                "redis_version": info.get("redis_version", "unknown"),
                "timestamp": current_time
            }
            
        except Exception as e:
            structured_logger.error(
                "Redis health check failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_time
            }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies."""
        # Add checks for external APIs, file storage, etc.
        return {
            "status": "healthy",
            "services": [],
            "timestamp": time.time()
        }
    
    def check_application_health(self) -> Dict[str, Any]:
        """Check application internal health."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Check if event loop is responsive
        loop_health = "healthy"
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop_health = "unhealthy"
        except Exception:
            loop_health = "unknown"
        
        return {
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "event_loop": loop_health,
            "timestamp": current_time
        }


# Global health checker instance
health_checker = HealthChecker()


@router.get("/healthz")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    This is typically used by load balancers for basic health checks.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok",
            "timestamp": time.time(),
            "service": "fastapi-menu-api"
        }
    )


@router.get("/readiness")
async def readiness_check(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """
    Readiness check endpoint.
    Verifies that all external dependencies (database, cache, etc.) are available.
    Used by orchestrators to determine if the application is ready to serve traffic.
    """
    start_time = time.time()
    checks = {}
    overall_status = "ready"
    
    try:
        # Check database
        structured_logger.debug("Starting database readiness check")
        db_check = await health_checker.check_database(db)
        checks["database"] = db_check
        
        if db_check["status"] != "healthy":
            overall_status = "not_ready"
        
        # Check Redis cache
        structured_logger.debug("Starting Redis readiness check")
        redis_check = await health_checker.check_redis(cache)
        checks["redis"] = redis_check
        
        if redis_check["status"] != "healthy":
            overall_status = "not_ready"
        
        # Check external services
        structured_logger.debug("Starting external services readiness check")
        external_check = await health_checker.check_external_services()
        checks["external_services"] = external_check
        
        if external_check["status"] != "healthy":
            overall_status = "not_ready"
        
        total_time = time.time() - start_time
        
        response_data = {
            "status": overall_status,
            "timestamp": time.time(),
            "check_duration": round(total_time, 4),
            "checks": checks
        }
        
        # Return appropriate status code
        if overall_status == "ready":
            structured_logger.info("Readiness check passed", duration=total_time)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data
            )
        else:
            structured_logger.warning(
                "Readiness check failed",
                duration=total_time,
                failed_checks=[k for k, v in checks.items() if v.get("status") != "healthy"]
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response_data
            )
    
    except Exception as e:
        total_time = time.time() - start_time
        structured_logger.error(
            "Readiness check error",
            error=str(e),
            error_type=type(e).__name__,
            duration=total_time
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "timestamp": time.time(),
                "check_duration": round(total_time, 4),
                "error": str(e),
                "checks": checks
            }
        )


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check endpoint.
    Verifies that the application is alive and responsive.
    Used by orchestrators to determine if the application should be restarted.
    """
    try:
        start_time = time.time()
        
        # Check application internal health
        app_health = health_checker.check_application_health()
        
        # Test async responsiveness
        await asyncio.sleep(0.001)  # Small async operation test
        
        total_time = time.time() - start_time
        
        response_data = {
            "status": "alive",
            "timestamp": time.time(),
            "check_duration": round(total_time, 4),
            "application": app_health
        }
        
        structured_logger.debug("Liveness check passed", duration=total_time)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
    
    except Exception as e:
        total_time = time.time() - start_time
        structured_logger.error(
            "Liveness check failed",
            error=str(e),
            error_type=type(e).__name__,
            duration=total_time
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "check_duration": round(total_time, 4),
                "error": str(e)
            }
        )


@router.get("/health/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """
    Detailed health check endpoint.
    Provides comprehensive health information about all system components.
    """
    start_time = time.time()
    
    try:
        # Run all health checks
        checks = {}
        
        # Application health
        checks["application"] = health_checker.check_application_health()
        
        # Database health
        checks["database"] = await health_checker.check_database(db)
        
        # Redis health
        checks["redis"] = await health_checker.check_redis(cache)
        
        # External services health
        checks["external_services"] = await health_checker.check_external_services()
        
        # Determine overall status
        unhealthy_checks = [
            name for name, check in checks.items() 
            if check.get("status") not in ["healthy", "alive", "ready"]
        ]
        
        overall_status = "healthy" if not unhealthy_checks else "degraded"
        
        total_time = time.time() - start_time
        
        response_data = {
            "status": overall_status,
            "timestamp": time.time(),
            "check_duration": round(total_time, 4),
            "checks": checks,
            "unhealthy_components": unhealthy_checks
        }
        
        if overall_status == "healthy":
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        structured_logger.info(
            "Detailed health check completed",
            status=overall_status,
            duration=total_time,
            unhealthy_components=unhealthy_checks
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    except Exception as e:
        total_time = time.time() - start_time
        structured_logger.error(
            "Detailed health check failed",
            error=str(e),
            error_type=type(e).__name__,
            duration=total_time
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "timestamp": time.time(),
                "check_duration": round(total_time, 4),
                "error": str(e)
            }
        )
