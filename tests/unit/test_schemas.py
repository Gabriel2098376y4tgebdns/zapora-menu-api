"""
Testes unitários para os schemas Pydantic.
"""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from my_menu_api import schemas


@pytest.mark.unit
class TestMenuItemSchemas:
    """Testes para schemas relacionados ao MenuItem."""
    
    def test_menu_item_base_valid(self):
        """Testa criação válida de MenuItemBase."""
        data = {
            "name": "Pizza Margherita",
            "description": "Pizza clássica italiana",
            "price": 25.90,
            "category": "Pizza",
            "available": True
        }
        
        item = schemas.MenuItemBase(**data)
        
        assert item.name == "Pizza Margherita"
        assert item.description == "Pizza clássica italiana"
        assert item.price == 25.90
        assert item.category == "Pizza"
        assert item.available is True
    
    def test_menu_item_base_price_validation(self):
        """Testa validação de preço no MenuItemBase."""
        # Preço válido
        valid_data = {
            "name": "Test Item",
            "description": "Test Description",
            "price": 10.50,
            "category": "Test"
        }
        item = schemas.MenuItemBase(**valid_data)
        assert item.price == 10.50
        
        # Preço zero - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemBase(
                name="Test", description="Test", price=0.0, category="Test"
            )
        assert "greater than 0" in str(exc_info.value)
        
        # Preço negativo - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemBase(
                name="Test", description="Test", price=-5.0, category="Test"
            )
        assert "greater than 0" in str(exc_info.value)
    
    def test_menu_item_base_string_validation(self):
        """Testa validação de strings no MenuItemBase."""
        # Nome muito longo - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemBase(
                name="x" * 101,  # Máximo é 100
                description="Test",
                price=10.0,
                category="Test"
            )
        assert "at most 100 characters" in str(exc_info.value)
        
        # Categoria muito longa - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemBase(
                name="Test",
                description="Test",
                price=10.0,
                category="x" * 51  # Máximo é 50
            )
        assert "at most 50 characters" in str(exc_info.value)
        
        # Descrição muito longa - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemBase(
                name="Test",
                description="x" * 501,  # Máximo é 500
                price=10.0,
                category="Test"
            )
        assert "at most 500 characters" in str(exc_info.value)
    
    def test_menu_item_create(self):
        """Testa schema MenuItemCreate."""
        data = {
            "name": "Hambúrguer Especial",
            "description": "Hambúrguer com ingredientes especiais",
            "price": 18.50,
            "category": "Hambúrguer",
            "available": True
        }
        
        item_create = schemas.MenuItemCreate(**data)
        
        # MenuItemCreate herda de MenuItemBase
        assert item_create.name == "Hambúrguer Especial"
        assert item_create.price == 18.50
    
    def test_menu_item_update_partial(self):
        """Testa schema MenuItemUpdate com campos opcionais."""
        # Update apenas do nome
        update_data = {"name": "Novo Nome"}
        item_update = schemas.MenuItemUpdate(**update_data)
        
        assert item_update.name == "Novo Nome"
        assert item_update.description is None
        assert item_update.price is None
        assert item_update.category is None
        assert item_update.available is None
        
        # Update de múltiplos campos
        update_data = {
            "name": "Pizza Atualizada",
            "price": 30.00,
            "available": False
        }
        item_update = schemas.MenuItemUpdate(**update_data)
        
        assert item_update.name == "Pizza Atualizada"
        assert item_update.price == 30.00
        assert item_update.available is False
        assert item_update.description is None  # Não fornecido
    
    def test_menu_item_update_price_validation(self):
        """Testa validação de preço no MenuItemUpdate."""
        # Preço válido
        update_data = {"price": 15.75}
        item_update = schemas.MenuItemUpdate(**update_data)
        assert item_update.price == 15.75
        
        # Preço inválido
        with pytest.raises(ValidationError):
            schemas.MenuItemUpdate(price=-10.0)
    
    def test_menu_item_complete(self):
        """Testa schema MenuItem completo."""
        item_id = uuid.uuid4()
        now = datetime.now()
        
        data = {
            "id": item_id,
            "name": "Pizza Completa",
            "description": "Pizza com todos os dados",
            "price": 28.90,
            "category": "Pizza",
            "available": True,
            "created_at": now,
            "updated_at": now
        }
        
        item = schemas.MenuItem(**data)
        
        assert item.id == item_id
        assert item.name == "Pizza Completa"
        assert item.created_at == now
        assert item.updated_at == now
    
    def test_menu_item_bulk_create(self):
        """Testa schema MenuItemBulkCreate."""
        items_data = [
            {
                "name": "Item 1",
                "description": "Descrição 1",
                "price": 10.0,
                "category": "Cat1"
            },
            {
                "name": "Item 2",
                "description": "Descrição 2",
                "price": 15.0,
                "category": "Cat2"
            }
        ]
        
        bulk_create = schemas.MenuItemBulkCreate(items=items_data)
        
        assert len(bulk_create.items) == 2
        assert bulk_create.items[0].name == "Item 1"
        assert bulk_create.items[1].price == 15.0
        
        # Lista vazia - deve falhar
        with pytest.raises(ValidationError):
            schemas.MenuItemBulkCreate(items=[])
        
        # Lista muito grande - deve falhar (máximo 1000)
        large_list = [{"name": f"Item {i}", "description": "Test", "price": 10.0, "category": "Test"} 
                     for i in range(1001)]
        with pytest.raises(ValidationError):
            schemas.MenuItemBulkCreate(items=large_list)


@pytest.mark.unit
class TestUserSchemas:
    """Testes para schemas relacionados ao User."""
    
    def test_user_base_valid(self):
        """Testa criação válida de UserBase."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "role": "user"
        }
        
        user = schemas.UserBase(**data)
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == "user"
        assert user.is_active is True  # Valor padrão
    
    def test_user_base_email_validation(self):
        """Testa validação de email no UserBase."""
        # Email válido
        valid_data = {
            "email": "valid@example.com",
            "username": "testuser",
            "role": "user"
        }
        user = schemas.UserBase(**valid_data)
        assert user.email == "valid@example.com"
        
        # Email inválido - deve falhar
        with pytest.raises(ValidationError) as exc_info:
            schemas.UserBase(
                email="invalid-email",
                username="testuser",
                role="user"
            )
        assert "valid email" in str(exc_info.value).lower()
    
    def test_user_create(self):
        """Testa schema UserCreate."""
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "password123",
            "role": "manager"
        }
        
        user_create = schemas.UserCreate(**data)
        
        assert user_create.email == "new@example.com"
        assert user_create.username == "newuser"
        assert user_create.password == "password123"
        assert user_create.role == "manager"
    
    def test_user_update(self):
        """Testa schema UserUpdate."""
        # Update parcial
        update_data = {"email": "updated@example.com"}
        user_update = schemas.UserUpdate(**update_data)
        
        assert user_update.email == "updated@example.com"
        assert user_update.username is None
        assert user_update.role is None
    
    def test_password_change(self):
        """Testa schema PasswordChange."""
        data = {
            "current_password": "oldpass123",
            "new_password": "NewPass123!"
        }
        
        password_change = schemas.PasswordChange(**data)
        
        assert password_change.current_password == "oldpass123"
        assert password_change.new_password == "NewPass123!"


@pytest.mark.unit
class TestAuditLogSchemas:
    """Testes para schemas relacionados ao AuditLog."""
    
    def test_audit_log_base(self):
        """Testa schema AuditLogBase."""
        data = {
            "action": "CREATE",
            "table_name": "menu_items",
            "record_id": str(uuid.uuid4()),
            "new_values": '{"name": "Test Item"}',
            "username": "testuser",
            "user_role": "admin",
            "ip_address": "192.168.1.1",
            "endpoint": "/menu-items"
        }
        
        audit_log = schemas.AuditLogBase(**data)
        
        assert audit_log.action == "CREATE"
        assert audit_log.table_name == "menu_items"
        assert audit_log.new_values == '{"name": "Test Item"}'
        assert audit_log.username == "testuser"
        assert audit_log.user_role == "admin"
    
    def test_audit_log_create(self):
        """Testa schema AuditLogCreate."""
        user_id = uuid.uuid4()
        data = {
            "action": "UPDATE",
            "table_name": "users",
            "record_id": str(uuid.uuid4()),
            "old_values": '{"email": "old@test.com"}',
            "new_values": '{"email": "new@test.com"}',
            "user_id": user_id
        }
        
        audit_create = schemas.AuditLogCreate(**data)
        
        assert audit_create.action == "UPDATE"
        assert audit_create.user_id == user_id


@pytest.mark.unit
class TestImageSchemas:
    """Testes para schemas relacionados a imagens."""
    
    def test_image_upload_response(self):
        """Testa schema ImageUploadResponse."""
        data = {
            "filename": "test_image.jpg",
            "url": "http://localhost:8000/static/test_image.jpg",
            "message": "Upload successful",
            "sizes": {
                "thumbnail": "http://localhost:8000/static/thumbnails/test_image.jpg",
                "small": "http://localhost:8000/static/small/test_image.jpg"
            }
        }
        
        response = schemas.ImageUploadResponse(**data)
        
        assert response.filename == "test_image.jpg"
        assert response.url == "http://localhost:8000/static/test_image.jpg"
        assert response.message == "Upload successful"
        assert "thumbnail" in response.sizes
        assert "small" in response.sizes


@pytest.mark.unit
class TestTokenSchemas:
    """Testes para schemas relacionados a tokens."""
    
    def test_token(self):
        """Testa schema Token."""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer"
        }
        
        token = schemas.Token(**data)
        
        assert token.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        assert token.token_type == "bearer"
    
    def test_token_data(self):
        """Testa schema TokenData."""
        data = {"username": "testuser"}
        
        token_data = schemas.TokenData(**data)
        
        assert token_data.username == "testuser"
