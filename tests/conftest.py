"""
Configurações compartilhadas para todos os testes.
"""

import asyncio
import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import uuid

# Adicionar o diretório raiz ao Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from my_menu_api.main import app
from my_menu_api.database import Base, get_db
from my_menu_api import models
from my_menu_api.auth import create_access_token, get_password_hash

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from my_menu_api.database import Base, get_db
from my_menu_api.main import app
from my_menu_api.config import get_settings
from my_menu_api import models
from my_menu_api.auth import get_password_hash


# Configuração do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def anyio_backend():
    """Define o backend async para testes."""
    return "asyncio"


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Cria uma sessão de banco de dados de teste."""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpar todas as tabelas após cada teste
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cria um cliente de teste FastAPI."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Cria um cliente async de teste."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Cria um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_settings():
    """Mock das configurações para testes."""
    settings = MagicMock()
    settings.app_name = "Test Menu API"
    settings.app_version = "1.0.0-test"
    settings.debug = True
    settings.secret_key = "test-secret-key"
    settings.algorithm = "HS256"
    settings.access_token_expire_minutes = 30
    settings.MAX_BULK_ITEMS = 100
    return settings


# ============================================================================
# FIXTURES DE USUÁRIOS
# ============================================================================

@pytest.fixture
def admin_user(db_session: Session) -> models.User:
    """Cria um usuário admin para testes."""
    user = models.User(
        id=uuid.uuid4(),
        email="admin@test.com",
        username="admin_test",
        hashed_password=get_password_hash("admin123"),
        role=models.UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def manager_user(db_session: Session) -> models.User:
    """Cria um usuário manager para testes."""
    user = models.User(
        id=uuid.uuid4(),
        email="manager@test.com",
        username="manager_test",
        hashed_password=get_password_hash("manager123"),
        role=models.UserRole.MANAGER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session) -> models.User:
    """Cria um usuário regular para testes."""
    user = models.User(
        id=uuid.uuid4(),
        email="user@test.com",
        username="user_test",
        hashed_password=get_password_hash("user123"),
        role=models.UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# FIXTURES DE TOKENS
# ============================================================================

@pytest.fixture
def admin_token(admin_user: models.User) -> str:
    """Gera token JWT para usuário admin."""
    from my_menu_api.auth import create_access_token
    return create_access_token(data={"sub": admin_user.username})


@pytest.fixture
def manager_token(manager_user: models.User) -> str:
    """Gera token JWT para usuário manager."""
    from my_menu_api.auth import create_access_token
    return create_access_token(data={"sub": manager_user.username})


@pytest.fixture
def user_token(regular_user: models.User) -> str:
    """Gera token JWT para usuário regular."""
    from my_menu_api.auth import create_access_token
    return create_access_token(data={"sub": regular_user.username})


# ============================================================================
# FIXTURES DE MENU ITEMS
# ============================================================================

@pytest.fixture
def sample_menu_item(db_session: Session) -> models.MenuItem:
    """Cria um item de menu de exemplo."""
    item = models.MenuItem(
        id=uuid.uuid4(),
        name="Pizza Margherita",
        description="Pizza clássica com molho de tomate, mozzarella e manjericão",
        price=25.90,
        category="Pizza",
        available=True
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def multiple_menu_items(db_session: Session) -> list[models.MenuItem]:
    """Cria múltiplos itens de menu para testes."""
    items = [
        models.MenuItem(
            id=uuid.uuid4(),
            name="Hambúrguer Clássico",
            description="Hambúrguer com carne, alface, tomate e queijo",
            price=18.50,
            category="Hambúrguer",
            available=True
        ),
        models.MenuItem(
            id=uuid.uuid4(),
            name="Salada Caesar",
            description="Salada com alface romana, croutons e molho caesar",
            price=15.00,
            category="Salada",
            available=True
        ),
        models.MenuItem(
            id=uuid.uuid4(),
            name="Refrigerante",
            description="Coca-Cola 350ml",
            price=5.00,
            category="Bebida",
            available=False  # Item indisponível
        )
    ]
    
    for item in items:
        db_session.add(item)
    db_session.commit()
    
    for item in items:
        db_session.refresh(item)
    
    return items


# ============================================================================
# FIXTURES DE ARQUIVOS DE TESTE
# ============================================================================

@pytest.fixture
def sample_image_file(temp_dir: Path) -> Path:
    """Cria um arquivo de imagem de teste."""
    from PIL import Image
    
    # Criar uma imagem simples de teste
    image = Image.new('RGB', (100, 100), color='red')
    image_path = temp_dir / "test_image.jpg"
    image.save(image_path)
    return image_path


@pytest.fixture
def invalid_image_file(temp_dir: Path) -> Path:
    """Cria um arquivo que não é uma imagem válida."""
    file_path = temp_dir / "not_an_image.txt"
    file_path.write_text("This is not an image file")
    return file_path


# ============================================================================
# FIXTURES DE AUDIT LOG
# ============================================================================

@pytest.fixture
def sample_audit_log(db_session: Session, admin_user: models.User) -> models.AuditLog:
    """Cria um log de auditoria de exemplo."""
    audit_log = models.AuditLog(
        id=uuid.uuid4(),
        action="CREATE",
        table_name="menu_items",
        record_id=str(uuid.uuid4()),
        new_values='{"name": "Test Item", "price": 10.00}',
        user_id=admin_user.id,
        username=admin_user.username,
        user_role=admin_user.role.value,
        ip_address="127.0.0.1",
        endpoint="/menu-items"
    )
    db_session.add(audit_log)
    db_session.commit()
    db_session.refresh(audit_log)
    return audit_log
