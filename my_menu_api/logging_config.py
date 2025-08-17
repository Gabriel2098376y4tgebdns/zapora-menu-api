"""
Structured logging configuration using loguru with JSON formatting.
"""

import sys
import json
import time
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
import contextvars
from loguru import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for request tracking
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')


class StructuredLogger:
    """Structured logger configuration with JSON formatting."""
    
    def __init__(
        self,
        service_name: str = "fastapi-menu-api",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        json_format: bool = True
    ):
        self.service_name = service_name
        self.log_level = log_level
        self.log_file = log_file
        self.json_format = json_format
        
        # Remove default logger
        logger.remove()
        
        # Configure logger
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure loguru logger with structured format."""
        
        # JSON formatter for structured logging
        def json_formatter(record):
            """Custom JSON formatter for loguru."""
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "service": self.service_name,
                "logger": record["name"],
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"]
            }
            
            # Add request context if available
            request_id = request_id_var.get()
            if request_id:
                log_entry["request_id"] = request_id
            
            user_id = user_id_var.get()
            if user_id:
                log_entry["user_id"] = user_id
            
            # Add extra fields from record
            if record["extra"]:
                log_entry.update(record["extra"])
            
            # Add exception info if present
            if record["exception"]:
                log_entry["exception"] = {
                    "type": record["exception"].type.__name__,
                    "message": str(record["exception"].value),
                    "traceback": record["exception"].traceback.format()
                }
            
            return json.dumps(log_entry, default=str, ensure_ascii=False)
        
        # Human-readable formatter for development
        def human_formatter(record):
            """Human-readable formatter for development."""
            request_id = request_id_var.get()
            user_id = user_id_var.get()
            
            extra_info = ""
            if request_id:
                extra_info += f" [req:{request_id[:8]}]"
            if user_id:
                extra_info += f" [user:{user_id[:8]}]"
            
            return (
                f"<green>{record['time']:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                f"<level>{record['level']: <8}</level> | "
                f"<cyan>{self.service_name}</cyan> | "
                f"<cyan>{record['name']}</cyan>:<cyan>{record['function']}</cyan>:<cyan>{record['line']}</cyan>"
                f"{extra_info} - <level>{record['message']}</level>"
            )
        
        # Choose formatter based on configuration
        formatter = json_formatter if self.json_format else human_formatter
        
        # Console handler
        logger.add(
            sys.stdout,
            format=formatter,
            level=self.log_level,
            colorize=not self.json_format,
            backtrace=True,
            diagnose=True
        )
        
        # File handler (if specified)
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                str(log_path),
                format=json_formatter,  # Always use JSON for file logs
                level=self.log_level,
                rotation="100 MB",
                retention="30 days",
                compression="gz",
                backtrace=True,
                diagnose=True
            )
        
        # Error file handler
        if self.log_file:
            error_log_path = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
            logger.add(
                str(error_log_path),
                format=json_formatter,
                level="ERROR",
                rotation="50 MB",
                retention="90 days",
                compression="gz",
                backtrace=True,
                diagnose=True
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with structured format."""
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = {"/healthz", "/readiness", "/liveness", "/metrics"}
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response with structured data."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Extract request information
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Skip logging for health check endpoints
        should_log = not any(request.url.path.startswith(path) for path in self.excluded_paths)
        
        if should_log:
            # Log incoming request
            logger.info(
                "Incoming request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "headers": dict(request.headers),
                    "event_type": "request_start"
                }
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            if should_log:
                logger.info(
                    "Request completed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "process_time": round(process_time, 4),
                        "client_ip": client_ip,
                        "response_headers": dict(response.headers),
                        "event_type": "request_end"
                    }
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "event_type": "request_error"
                }
            )
            
            # Re-raise the exception
            raise
    
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


# Enhanced logger with context
class ContextLogger:
    """Enhanced logger with automatic context inclusion."""
    
    @staticmethod
    def info(message: str, **kwargs):
        """Log info message with context."""
        logger.info(message, extra=kwargs)
    
    @staticmethod
    def error(message: str, **kwargs):
        """Log error message with context."""
        logger.error(message, extra=kwargs)
    
    @staticmethod
    def warning(message: str, **kwargs):
        """Log warning message with context."""
        logger.warning(message, extra=kwargs)
    
    @staticmethod
    def debug(message: str, **kwargs):
        """Log debug message with context."""
        logger.debug(message, extra=kwargs)
    
    @staticmethod
    def critical(message: str, **kwargs):
        """Log critical message with context."""
        logger.critical(message, extra=kwargs)
    
    @staticmethod
    def with_user(user_id: str):
        """Set user context for logging."""
        user_id_var.set(user_id)
        return ContextLogger
    
    @staticmethod
    def bind(**kwargs):
        """Bind additional context to logger."""
        return logger.bind(**kwargs)


# Global structured logger instance
structured_logger = ContextLogger()


def setup_logging(
    service_name: str = "fastapi-menu-api",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
) -> StructuredLogger:
    """Setup structured logging for the application."""
    return StructuredLogger(
        service_name=service_name,
        log_level=log_level,
        log_file=log_file,
        json_format=json_format
    )


# Utility functions for common logging patterns
def log_api_call(
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log API call with standard format."""
    structured_logger.info(
        f"API call: {method} {endpoint}",
        endpoint=endpoint,
        method=method,
        user_id=user_id,
        event_type="api_call",
        **kwargs
    )


def log_database_operation(
    operation: str,
    table: str,
    duration: Optional[float] = None,
    **kwargs
):
    """Log database operation with standard format."""
    structured_logger.info(
        f"Database {operation}: {table}",
        operation=operation,
        table=table,
        duration=duration,
        event_type="database_operation",
        **kwargs
    )


def log_cache_operation(
    operation: str,
    key: str,
    hit: Optional[bool] = None,
    **kwargs
):
    """Log cache operation with standard format."""
    structured_logger.info(
        f"Cache {operation}: {key}",
        operation=operation,
        key=key,
        hit=hit,
        event_type="cache_operation",
        **kwargs
    )
