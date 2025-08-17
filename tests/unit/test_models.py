"""
Testes unitários para os modelos da aplicação.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from my_menu_api import models
from my_menu_api.auth import get_password_hash, verify_password


@pytest.mark.unit
class TestUserModel:
    """Testes para o modelo User."""
    
    def test_create_user(self, db_session: Session):
        """Testa criação básica de usuário."""
        user_id = uuid.uuid4()
        user = models.User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.USER,
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verificações
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == models.UserRole.USER
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
        assert verify_password("password123", user.hashed_password)
    
    def test_user_roles(self):
        """Testa os valores dos roles de usuário."""
        assert models.UserRole.ADMIN == "admin"
        assert models.UserRole.MANAGER == "manager"
        assert models.UserRole.USER == "user"
    
    def test_user_unique_constraints(self, db_session: Session):
        """Testa constraints únicos do modelo User."""
        user1 = models.User(
            id=uuid.uuid4(),
            email="unique@test.com",
            username="unique_user",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.USER
        )
        
        db_session.add(user1)
        db_session.commit()
        
        # Tentar criar usuário com email duplicado
        user2 = models.User(
            id=uuid.uuid4(),
            email="unique@test.com",  # Email duplicado
            username="another_user",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.USER
        )
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Violação de constraint
            db_session.commit()
    
    def test_user_repr(self, db_session: Session):
        """Testa representação string do usuário."""
        user = models.User(
            id=uuid.uuid4(),
            email="repr@test.com",
            username="repr_user",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.ADMIN
        )
        
        # O modelo User não tem __repr__ definido, mas podemos testar atributos
        assert "repr@test.com" in str(user.email)
        assert "repr_user" in str(user.username)


@pytest.mark.unit
class TestMenuItemModel:
    """Testes para o modelo MenuItem."""
    
    def test_create_menu_item(self, db_session: Session):
        """Testa criação básica de item do menu."""
        item_id = uuid.uuid4()
        item = models.MenuItem(
            id=item_id,
            name="Pizza Margherita",
            description="Pizza clássica italiana",
            price=25.90,
            category="Pizza",
            available=True
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Verificações
        assert item.id == item_id
        assert item.name == "Pizza Margherita"
        assert item.description == "Pizza clássica italiana"
        assert item.price == 25.90
        assert item.category == "Pizza"
        assert item.available is True
        assert item.created_at is not None
        assert item.updated_at is not None
        
        # Campos de imagem devem ser None por padrão
        assert item.image_filename is None
        assert item.image_path is None
        assert item.image_url is None
    
    def test_menu_item_with_image(self, db_session: Session):
        """Testa item do menu com campos de imagem."""
        item = models.MenuItem(
            id=uuid.uuid4(),
            name="Hambúrguer Especial",
            description="Hambúrguer com ingredientes especiais",
            price=18.50,
            category="Hambúrguer",
            available=True,
            image_filename="hamburger_special.jpg",
            image_path="/uploads/originals/hamburger_special.jpg",
            image_url="http://localhost:8000/static/originals/hamburger_special.jpg"
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Verificar campos de imagem
        assert item.image_filename == "hamburger_special.jpg"
        assert item.image_path == "/uploads/originals/hamburger_special.jpg"
        assert item.image_url == "http://localhost:8000/static/originals/hamburger_special.jpg"
    
    def test_menu_item_price_validation(self, db_session: Session):
        """Testa que preços válidos são aceitos."""
        # Preço com duas casas decimais
        item1 = models.MenuItem(
            id=uuid.uuid4(),
            name="Item 1",
            description="Descrição",
            price=10.99,
            category="Teste"
        )
        
        # Preço inteiro
        item2 = models.MenuItem(
            id=uuid.uuid4(),
            name="Item 2",
            description="Descrição",
            price=15.0,
            category="Teste"
        )
        
        db_session.add_all([item1, item2])
        db_session.commit()
        
        db_session.refresh(item1)
        db_session.refresh(item2)
        
        assert item1.price == 10.99
        assert item2.price == 15.0
    
    def test_menu_item_repr(self, db_session: Session):
        """Testa representação string do item."""
        item = models.MenuItem(
            id=uuid.uuid4(),
            name="Test Item",
            description="Test Description",
            price=10.00,
            category="Test Category"
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        repr_str = repr(item)
        assert "MenuItem" in repr_str
        assert "Test Item" in repr_str
        assert "Test Category" in repr_str


@pytest.mark.unit
class TestAuditLogModel:
    """Testes para o modelo AuditLog."""
    
    def test_create_audit_log(self, db_session: Session, admin_user: models.User):
        """Testa criação de log de auditoria."""
        log_id = uuid.uuid4()
        audit_log = models.AuditLog(
            id=log_id,
            action="CREATE",
            table_name="menu_items",
            record_id=str(uuid.uuid4()),
            new_values='{"name": "New Item", "price": 20.00}',
            user_id=admin_user.id,
            username=admin_user.username,
            user_role=admin_user.role.value,
            ip_address="192.168.1.100",
            endpoint="/menu-items"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        db_session.refresh(audit_log)
        
        # Verificações
        assert audit_log.id == log_id
        assert audit_log.action == "CREATE"
        assert audit_log.table_name == "menu_items"
        assert audit_log.new_values == '{"name": "New Item", "price": 20.00}'
        assert audit_log.old_values is None  # CREATE não tem valores antigos
        assert audit_log.user_id == admin_user.id
        assert audit_log.username == admin_user.username
        assert audit_log.user_role == admin_user.role.value
        assert audit_log.ip_address == "192.168.1.100"
        assert audit_log.endpoint == "/menu-items"
        assert audit_log.created_at is not None
    
    def test_audit_log_update_action(self, db_session: Session, manager_user: models.User):
        """Testa log de auditoria para ação UPDATE."""
        audit_log = models.AuditLog(
            id=uuid.uuid4(),
            action="UPDATE",
            table_name="menu_items",
            record_id=str(uuid.uuid4()),
            old_values='{"name": "Old Name", "price": 15.00}',
            new_values='{"name": "New Name", "price": 18.00}',
            changed_fields='["name", "price"]',
            user_id=manager_user.id,
            username=manager_user.username,
            user_role=manager_user.role.value,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0...",
            endpoint="/menu-items/123"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        db_session.refresh(audit_log)
        
        # Verificações específicas para UPDATE
        assert audit_log.action == "UPDATE"
        assert audit_log.old_values is not None
        assert audit_log.new_values is not None
        assert audit_log.changed_fields == '["name", "price"]'
        assert audit_log.user_agent == "Mozilla/5.0..."
    
    def test_audit_log_delete_action(self, db_session: Session, admin_user: models.User):
        """Testa log de auditoria para ação DELETE."""
        audit_log = models.AuditLog(
            id=uuid.uuid4(),
            action="DELETE",
            table_name="menu_items",
            record_id=str(uuid.uuid4()),
            old_values='{"name": "Deleted Item", "price": 25.00}',
            user_id=admin_user.id,
            username=admin_user.username,
            user_role=admin_user.role.value,
            ip_address="172.16.0.1",
            endpoint="/menu-items/456"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        db_session.refresh(audit_log)
        
        # Verificações específicas para DELETE
        assert audit_log.action == "DELETE"
        assert audit_log.old_values is not None
        assert audit_log.new_values is None  # DELETE não tem novos valores


@pytest.mark.unit
class TestGUIDTypeDecorator:
    """Testes para o tipo customizado GUID."""
    
    def test_guid_creation(self, db_session: Session):
        """Testa que UUIDs são criados e armazenados corretamente."""
        user = models.User(
            email="guid@test.com",
            username="guid_test",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.USER
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verificar que o ID é um UUID válido
        assert isinstance(user.id, uuid.UUID)
        assert len(str(user.id)) == 36  # Formato padrão UUID
        
        # Recuperar do banco e verificar
        retrieved_user = db_session.query(models.User).filter(
            models.User.id == user.id
        ).first()
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert isinstance(retrieved_user.id, uuid.UUID)
