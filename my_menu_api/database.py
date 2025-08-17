"""
Configuração do banco de dados com SQLAlchemy.
Agora usa configurações dinâmicas e remove duplicação da função get_db.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# Engine com configurações dinâmicas
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    pool_size=settings.connection_pool_size,
    max_overflow=settings.max_overflow,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    echo=settings.debug  # Log SQL queries em desenvolvimento
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados.
    Garante que a sessão seja sempre fechada após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()