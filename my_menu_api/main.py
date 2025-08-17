"""
Ponto de entrada principal da aplicação FastAPI.
Configuração da aplicação e inclusão de routers.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from . import models
from .database import engine
from .config import get_settings
from .routers import menu_items, auth, audit, images

settings = get_settings()

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    startup_start = time.time()
    
    try:
        logger.info("Starting application initialization")
        
        # Initialize production components if available
        try:
            from .logging_config import configure_logging
            configure_logging()
            logger.info("Structured logging configured")
        except ImportError:
            logger.info("Using basic logging (structured logging not available)")
        
        try:
            from .cache import init_cache
            await init_cache(app)
            logger.info("Cache initialized")
        except ImportError:
            logger.info("Cache not available")
        
        # Run database migrations in production
        if not settings.debug:
            try:
                from .migration_utils import run_migrations
                migration_success = run_migrations()
                if migration_success:
                    logger.info("Database migrations completed")
                else:
                    logger.warning("Database migrations failed")
            except ImportError:
                logger.info("Migrations not available")
        
        # Create tables (fallback)
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified")
        
        # Create upload directories
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for subdir in ["originals", "large", "medium", "small", "thumbnails"]:
            (upload_dir / subdir).mkdir(exist_ok=True)
        
        logger.info("Upload directories created")
        
        # Setup metrics if available
        try:
            from .metrics import setup_metrics
            setup_metrics(app)
            logger.info("Metrics collection initialized")
        except ImportError:
            logger.info("Metrics collection not available")
        
        startup_time = time.time() - startup_start
        logger.info(
            f"Application startup completed in {startup_time:.4f}s - "
            f"{settings.app_name} v{settings.app_version}"
        )
        
        print(f"🚀 {settings.app_name} v{settings.app_version} iniciada!")
        print(f"📚 Documentação: http://localhost:8000/docs")
        print(f"🔍 Health checks: http://localhost:8000/healthz")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Starting application shutdown")
        
        try:
            from .cache import close_cache
            await close_cache()
            logger.info("Cache connections closed")
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error during cache shutdown: {e}")
        
        logger.info(f"Application shutdown completed - {settings.app_name}")
        print(f"👋 {settings.app_name} encerrada!")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="API RESTful para gerenciamento de cardápio com infraestrutura de produção",
    contact={"name": "Suporte", "email": "suporte@menuapi.com"},
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add production middleware if available
try:
    from .logging_config import LoggingMiddleware
    app.add_middleware(LoggingMiddleware)
    logger.info("Logging middleware added")
except ImportError:
    pass

try:
    from .rate_limiting import RateLimitMiddleware
    # Create a basic config for rate limiting
    rate_limit_config = {
        "default": {"requests": 100, "window": 60},
        "auth/login": {"requests": 5, "window": 60},
        "images/upload": {"requests": 10, "window": 300}
    }
    app.add_middleware(RateLimitMiddleware, config=rate_limit_config)
    logger.info("Rate limiting middleware added")
except ImportError:
    pass

# CORS middleware
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Serve static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include health checks if available
try:
    from .health import router as health_router
    app.include_router(health_router)
    logger.info("Health check endpoints added")
except ImportError:
    # Basic health check
    @app.get("/healthz")
    async def basic_health_check():
        """Basic health check endpoint."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(menu_items.router, prefix="/menu-items", tags=["menu"])
app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        metrics_data = generate_latest()
        return JSONResponse(
            content=metrics_data.decode('utf-8'),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        return JSONResponse(
            content={"error": "Metrics not available"},
            status_code=503
        )
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return JSONResponse(
            content={"error": "Metrics temporarily unavailable"},
            status_code=503
        )


@app.get("/health")
async def health_check():
    """Legacy health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Bem-vindo à {settings.app_name}!",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "features": [
            "JWT Authentication",
            "Image Upload & Processing",
            "Audit Logging",
            "Redis Caching (optional)",
            "Rate Limiting (optional)",
            "Structured Logging (optional)",
            "Prometheus Metrics (optional)",
            "Health Checks",
            "Database Migrations (optional)"
        ],
        "endpoints": {
            "docs": "/docs" if settings.debug else "Available only in development",
            "health": "/health",
            "metrics": "/metrics",
            "menu_items": "/menu-items",
            "auth": "/auth",
            "images": "/images",
            "audit": "/audit"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "my_menu_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
