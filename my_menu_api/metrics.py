"""
Prometheus metrics configuration for FastAPI application.
"""

import time
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from fastapi import FastAPI, Request, Response
from fastapi.responses import Response as FastAPIResponse
from starlette.middleware.base import BaseHTTPMiddleware
import psutil
import threading

# Custom registry for application metrics
app_registry = CollectorRegistry()

# HTTP Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=app_registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Time spent processing HTTP requests',
    ['method', 'endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=app_registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint'],
    registry=app_registry
)

# Application metrics
app_exceptions_total = Counter(
    'app_exceptions_total',
    'Total number of application exceptions',
    ['exception_type', 'endpoint'],
    registry=app_registry
)

# Database metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=app_registry
)

database_operations_total = Counter(
    'database_operations_total',
    'Total number of database operations',
    ['operation', 'table'],
    registry=app_registry
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Time spent on database operations',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=app_registry
)

# Cache metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation', 'result'],
    registry=app_registry
)

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (0-1)',
    registry=app_registry
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['result', 'method'],
    registry=app_registry
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active user sessions',
    registry=app_registry
)

# System metrics
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=app_registry
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=app_registry
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['mount_point'],
    registry=app_registry
)

# Application info
app_info = Info(
    'app_info',
    'Application information',
    registry=app_registry
)

# Business metrics
menu_items_total = Gauge(
    'menu_items_total',
    'Total number of menu items',
    ['category', 'status'],
    registry=app_registry
)

user_registrations_total = Counter(
    'user_registrations_total',
    'Total number of user registrations',
    ['role'],
    registry=app_registry
)

image_uploads_total = Counter(
    'image_uploads_total',
    'Total number of image uploads',
    ['status'],
    registry=app_registry
)

audit_logs_total = Counter(
    'audit_logs_total',
    'Total number of audit log entries',
    ['action', 'resource_type'],
    registry=app_registry
)


class PrometheusMetrics:
    """Prometheus metrics collector and manager."""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_requests: Dict[str, int] = {}
        self._system_metrics_thread = None
        self._stop_system_metrics = False
    
    def start_system_metrics_collection(self):
        """Start background thread for system metrics collection."""
        if self._system_metrics_thread is None or not self._system_metrics_thread.is_alive():
            self._stop_system_metrics = False
            self._system_metrics_thread = threading.Thread(
                target=self._collect_system_metrics,
                daemon=True
            )
            self._system_metrics_thread.start()
    
    def stop_system_metrics_collection(self):
        """Stop system metrics collection."""
        self._stop_system_metrics = True
        if self._system_metrics_thread:
            self._system_metrics_thread.join(timeout=5)
    
    def _collect_system_metrics(self):
        """Collect system metrics in background thread."""
        while not self._stop_system_metrics:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                system_cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.used)
                
                # Disk usage
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        system_disk_usage.labels(mount_point=partition.mountpoint).set(usage.used)
                    except (PermissionError, OSError):
                        continue
                
                time.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                time.sleep(60)  # Wait longer on error
    
    def record_request_start(self, method: str, endpoint: str):
        """Record start of HTTP request."""
        key = f"{method}:{endpoint}"
        self.active_requests[key] = self.active_requests.get(key, 0) + 1
        http_requests_in_progress.labels(method=method, endpoint=endpoint).set(
            self.active_requests[key]
        )
    
    def record_request_end(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record end of HTTP request."""
        # Decrement active requests
        key = f"{method}:{endpoint}"
        self.active_requests[key] = max(0, self.active_requests.get(key, 0) - 1)
        http_requests_in_progress.labels(method=method, endpoint=endpoint).set(
            self.active_requests[key]
        )
        
        # Record metrics
        http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
    
    def record_exception(self, exception_type: str, endpoint: str):
        """Record application exception."""
        app_exceptions_total.labels(
            exception_type=exception_type,
            endpoint=endpoint
        ).inc()
    
    def record_database_operation(self, operation: str, table: str, duration: float):
        """Record database operation."""
        database_operations_total.labels(operation=operation, table=table).inc()
        database_operation_duration_seconds.labels(
            operation=operation, 
            table=table
        ).observe(duration)
    
    def update_database_connections(self, count: int):
        """Update active database connections count."""
        database_connections_active.set(count)
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation."""
        result = "hit" if hit else "miss"
        cache_operations_total.labels(operation=operation, result=result).inc()
        
        # Update hit ratio
        if operation == "get":
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            
            total_gets = self.cache_hits + self.cache_misses
            if total_gets > 0:
                hit_ratio = self.cache_hits / total_gets
                cache_hit_ratio.set(hit_ratio)
    
    def record_auth_attempt(self, success: bool, method: str = "jwt"):
        """Record authentication attempt."""
        result = "success" if success else "failure"
        auth_attempts_total.labels(result=result, method=method).inc()
    
    def update_active_sessions(self, count: int):
        """Update active sessions count."""
        active_sessions.set(count)
    
    def update_menu_items_count(self, category: str, status: str, count: int):
        """Update menu items count."""
        menu_items_total.labels(category=category, status=status).set(count)
    
    def record_user_registration(self, role: str):
        """Record user registration."""
        user_registrations_total.labels(role=role).inc()
    
    def record_image_upload(self, success: bool):
        """Record image upload."""
        status = "success" if success else "failure"
        image_uploads_total.labels(status=status).inc()
    
    def record_audit_log(self, action: str, resource_type: str):
        """Record audit log entry."""
        audit_logs_total.labels(action=action, resource_type=resource_type).inc()
    
    def set_app_info(self, version: str, environment: str):
        """Set application information."""
        app_info.info({
            'version': version,
            'environment': environment,
            'service': 'fastapi-menu-api'
        })


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""
    
    def __init__(self, app, metrics: PrometheusMetrics):
        super().__init__(app)
        self.metrics = metrics
    
    async def dispatch(self, request: Request, call_next):
        """Collect metrics for each request."""
        method = request.method
        endpoint = self._get_endpoint_name(request)
        
        # Record request start
        start_time = time.time()
        self.metrics.record_request_start(method, endpoint)
        
        try:
            response = await call_next(request)
            
            # Record successful request
            duration = time.time() - start_time
            self.metrics.record_request_end(method, endpoint, response.status_code, duration)
            
            return response
            
        except Exception as e:
            # Record exception
            duration = time.time() - start_time
            exception_type = type(e).__name__
            
            self.metrics.record_exception(exception_type, endpoint)
            self.metrics.record_request_end(method, endpoint, 500, duration)
            
            raise
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request."""
        path = request.url.path
        
        # Replace path parameters with placeholders
        if hasattr(request, 'path_info'):
            route = request.path_info.get('route')
            if route:
                return route.path
        
        # Fallback to path with ID parameters replaced
        import re
        # Replace UUIDs and numeric IDs with placeholders
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path


# Global metrics instance
metrics = PrometheusMetrics()


def setup_metrics(app: FastAPI, version: str = "1.0.0", environment: str = "development"):
    """Setup Prometheus metrics for FastAPI application."""
    
    # Set application info
    metrics.set_app_info(version, environment)
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware, metrics=metrics)
    
    # Start system metrics collection
    metrics.start_system_metrics_collection()
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        # Combine default registry and app registry
        from prometheus_client.registry import CollectorRegistry
        combined_registry = CollectorRegistry()
        
        # Add all collectors from app registry
        for collector in app_registry._collector_to_names:
            combined_registry.register(collector)
        
        return Response(
            generate_latest(combined_registry),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return metrics


def get_metrics() -> PrometheusMetrics:
    """Get global metrics instance."""
    return metrics
