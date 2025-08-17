"""
Configurações dinâmicas da aplicação usando Pydantic Settings.
Permite flexibilidade via variáveis de ambiente sem hardcoding.
"""

from functools import lru_cache
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação com valores padrão para desenvolvimento."""
    
    # Database
    database_url: str = "sqlite:///./sql_app.db"
    
    # API Metadata
    app_name: str = "Menu API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Performance
    MAX_BULK_ITEMS: int = 1000
    connection_pool_size: int = 20
    max_overflow: int = 30
    
    # Segurança - JWT
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Password hashing
    bcrypt_rounds: int = 12
    
    # Admin padrão
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )
    
    def model_post_init(self, __context) -> None:
        """Validações pós-inicialização para segurança."""
        # Validar que secrets obrigatórios foram configurados
        if not self.secret_key:
            raise ValueError(
                "SECRET_KEY não pode estar vazio! Configure a variável de ambiente SECRET_KEY."
            )
        
        if not self.default_admin_password:
            raise ValueError(
                "ADMIN_PASSWORD não pode estar vazio! Configure a variável de ambiente ADMIN_PASSWORD."
            )
        
        # Validar que não estamos usando valores inseguros
        insecure_keys = [
            "development-key-change-in-production",
            "your-super-secret-jwt-key-change-this-in-production-please",
            "secret",
            "jwt-secret-key"
        ]
        
        if self.secret_key in insecure_keys:
            raise ValueError(
                f"SECRET_KEY '{self.secret_key}' é insegura! Use uma chave forte e única."
            )
        
        insecure_passwords = ["admin123", "password", "123456", "admin"]
        
        if self.default_admin_password in insecure_passwords:
            raise ValueError(
                f"ADMIN_PASSWORD é insegura! Use uma senha forte."
            )


@lru_cache()
def get_settings() -> Settings:
    """
    Cria e cacheia uma instância das configurações.
    O cache evita recarregar as configurações a cada chamada.
    """
    return Settings()


# Instância global das configurações para uso em toda a aplicação
settings = get_settings()
