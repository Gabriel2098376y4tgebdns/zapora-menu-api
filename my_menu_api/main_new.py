"""
Ponto de entrada principal da aplicação FastAPI.
Configuração da aplicação e inclusão de routers.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from . import models
from .database import engine
from .config import get_settings
from .routers import menu_items, auth, audit, images


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    # Criar diretório para uploads se não existir
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Criar subdiretórios para imagens
    for subdir in ["originals", "large", "medium", "small", "thumbnails"]:
        (upload_dir / subdir).mkdir(exist_ok=True)
    
    # Criar tabelas se não existirem
    models.Base.metadata.create_all(bind=engine)
    
    print(f"🚀 {settings.app_name} iniciada!")
    print(f"📚 Documentação disponível em: http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print(f"👋 {settings.app_name} encerrada!")


# Criar a aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API RESTful para gerenciamento de cardápio com autenticação JWT",
    contact={"name": "Suporte", "email": "suporte@menuapi.com"},
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,  # Docs apenas em desenvolvimento
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware de CORS
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especificar domínios
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Servir arquivos estáticos (uploads)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Incluir routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(menu_items.router, prefix="/menu-items", tags=["menu"])
app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "message": f"Bem-vindo à {settings.app_name}!",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentação disponível apenas em desenvolvimento",
        "endpoints": {
            "health": "/health",
            "menu_items": "/menu-items",
            "auth": "/auth",
            "images": "/images",
            "audit": "/audit"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
