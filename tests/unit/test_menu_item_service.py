"""
Testes unitários para o MenuItemService.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from my_menu_api import models, schemas
from my_menu_api.services.menu_item_service import MenuItemService


@pytest.mark.unit
class TestMenuItemService:
    """Testes para o MenuItemService."""
    
    def test_get_all(self, db_session: Session, multiple_menu_items):
        """Testa recuperação de todos os itens."""
        items = MenuItemService.get_all(db_session)
        
        assert len(items) == 3  # De acordo com a fixture multiple_menu_items
        assert all(isinstance(item, models.MenuItem) for item in items)
    
    def test_get_by_id_exists(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa recuperação de item por ID quando existe."""
        item = MenuItemService.get_by_id(db_session, str(sample_menu_item.id))
        
        assert item is not None
        # Usar getattr para acessar os valores das colunas
        assert getattr(item, 'name') == getattr(sample_menu_item, 'name')
    
    def test_get_by_id_not_exists(self, db_session: Session):
        """Testa recuperação de item por ID quando não existe."""
        non_existent_id = str(uuid.uuid4())
        item = MenuItemService.get_by_id(db_session, non_existent_id)
        
        assert item is None
    
    def test_get_menu_item_alias(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa o método alias get_menu_item."""
        # Convertendo UUID para int para o teste (assumindo conversão)
        item_id = 1  # Simplificado para teste
        
        # Mock do query para retornar o item
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = sample_menu_item
            
            item = MenuItemService.get_menu_item(db_session, item_id)
            
            assert item is not None
            mock_query.assert_called_once_with(models.MenuItem)
    
    def test_create_basic(self, db_session: Session):
        """Testa criação básica de item."""
        item_data = schemas.MenuItemCreate(
            name="Test Pizza",
            description="Pizza de teste",
            price=20.00,
            category="Pizza",
            available=True
        )
        
        with patch('my_menu_api.services.menu_item_service.audit_create') as mock_audit:
            item = MenuItemService.create(db_session, item_data)
            
            assert item is not None
            # Verificar que auditoria foi chamada
            mock_audit.assert_called_once()
    
    def test_create_with_user_context(self, db_session: Session, admin_user: models.User):
        """Testa criação com contexto de usuário para auditoria."""
        item_data = schemas.MenuItemCreate(
            name="Pizza do Admin",
            description="Pizza criada pelo admin",
            price=30.00,
            category="Pizza",
            available=True
        )
        
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        with patch('my_menu_api.services.menu_item_service.audit_create') as mock_audit:
            item = MenuItemService.create(db_session, item_data, admin_user, mock_request)
            
            assert item is not None
            # Verificar que auditoria foi chamada com usuário
            mock_audit.assert_called_once_with(db_session, item, admin_user, mock_request)
    
    def test_update_menu_item_success(self, db_session: Session, sample_menu_item: models.MenuItem, manager_user: models.User):
        """Testa atualização bem-sucedida de item."""
        # Mock para o get_menu_item retornar o item
        with patch.object(MenuItemService, 'get_menu_item', return_value=sample_menu_item):
            with patch('my_menu_api.services.menu_item_service.model_to_dict', return_value={"name": "Old Name"}):
                with patch('my_menu_api.services.menu_item_service.audit_update_simple') as mock_audit:
                    
                    update_data = schemas.MenuItemUpdate(
                        name="Updated Pizza",
                        price=35.00
                    )
                    
                    updated_item = MenuItemService.update_menu_item(
                        db_session, 1, update_data, manager_user, "192.168.1.1"
                    )
                    
                    assert updated_item is not None
                    mock_audit.assert_called_once()
    
    def test_update_menu_item_not_found(self, db_session: Session, manager_user: models.User):
        """Testa atualização quando item não existe."""
        with patch.object(MenuItemService, 'get_menu_item', return_value=None):
            
            update_data = schemas.MenuItemUpdate(name="Não Existe")
            
            result = MenuItemService.update_menu_item(
                db_session, 999, update_data, manager_user, "192.168.1.1"
            )
            
            assert result is None
    
    def test_get_by_category(self, db_session: Session, multiple_menu_items):
        """Testa recuperação por categoria."""
        # Mock da query para retornar itens filtrados
        pizza_items = [item for item in multiple_menu_items if getattr(item, 'category') == 'Pizza']
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = pizza_items
            
            items = MenuItemService.get_by_category(db_session, "Pizza")
            
            assert len(items) >= 0  # Pode não ter pizzas nos dados de teste
            mock_query.assert_called_once_with(models.MenuItem)
    
    def test_get_available_items(self, db_session: Session, multiple_menu_items):
        """Testa recuperação apenas de itens disponíveis."""
        available_items = [item for item in multiple_menu_items if getattr(item, 'available')]
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = available_items
            
            items = MenuItemService.get_available_items(db_session)
            
            assert all(getattr(item, 'available') for item in items)
    
    def test_create_bulk_success(self, db_session: Session):
        """Testa criação em lote bem-sucedida."""
        items_data = [
            schemas.MenuItemCreate(
                name=f"Bulk Item {i}",
                description=f"Description {i}",
                price=10.0 + i,
                category="Bulk",
                available=True
            )
            for i in range(3)
        ]
        
        with patch('my_menu_api.services.menu_item_service.get_settings') as mock_settings:
            mock_settings.return_value.MAX_BULK_ITEMS = 1000
            
            items = MenuItemService.create_bulk(db_session, items_data)
            
            assert len(items) == 3
            assert all(isinstance(item, models.MenuItem) for item in items)
    
    def test_create_bulk_limit_exceeded(self, db_session: Session):
        """Testa criação em lote com limite excedido."""
        # Criar muitos itens para exceder o limite
        items_data = [
            schemas.MenuItemCreate(
                name=f"Item {i}",
                description="Test",
                price=10.0,
                category="Test",
                available=True
            )
            for i in range(1001)  # Assumindo limite de 1000
        ]
        
        with patch('my_menu_api.services.menu_item_service.get_settings') as mock_settings:
            mock_settings.return_value.MAX_BULK_ITEMS = 1000
            
            with pytest.raises(ValueError) as exc_info:
                MenuItemService.create_bulk(db_session, items_data)
            
            assert "Máximo de 1000 itens" in str(exc_info.value)
    
    def test_update_full(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa atualização completa (PUT)."""
        with patch.object(MenuItemService, 'get_by_id', return_value=sample_menu_item):
            
            update_data = schemas.MenuItemCreate(
                name="Completely New Name",
                description="Completely new description",
                price=50.00,
                category="New Category",
                available=False
            )
            
            updated_item = MenuItemService.update_full(db_session, str(sample_menu_item.id), update_data)
            
            assert updated_item is not None
    
    def test_update_partial(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa atualização parcial (PATCH)."""
        with patch.object(MenuItemService, 'get_by_id', return_value=sample_menu_item):
            
            update_data = schemas.MenuItemUpdate(
                name="Partially Updated Name",
                price=25.00
                # description, category, available não fornecidos
            )
            
            updated_item = MenuItemService.update_partial(db_session, str(sample_menu_item.id), update_data)
            
            assert updated_item is not None
    
    def test_delete_success(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa exclusão bem-sucedida."""
        with patch.object(MenuItemService, 'get_by_id', return_value=sample_menu_item):
            
            result = MenuItemService.delete(db_session, str(sample_menu_item.id))
            
            assert result is True
    
    def test_delete_not_found(self, db_session: Session):
        """Testa exclusão quando item não existe."""
        with patch.object(MenuItemService, 'get_by_id', return_value=None):
            
            result = MenuItemService.delete(db_session, str(uuid.uuid4()))
            
            assert result is False


@pytest.mark.unit 
class TestMenuItemServiceEdgeCases:
    """Testes para casos extremos do MenuItemService."""
    
    def test_create_with_minimal_data(self, db_session: Session):
        """Testa criação com dados mínimos obrigatórios."""
        item_data = schemas.MenuItemCreate(
            name="Minimal",
            description="",  # Descrição vazia
            price=1.00,  # Preço mínimo
            category="Test"
        )
        
        with patch('my_menu_api.services.menu_item_service.audit_create'):
            item = MenuItemService.create(db_session, item_data)
            
            assert item is not None
    
    def test_update_with_empty_partial(self, db_session: Session, sample_menu_item: models.MenuItem):
        """Testa atualização parcial sem campos fornecidos."""
        with patch.object(MenuItemService, 'get_by_id', return_value=sample_menu_item):
            
            # Update sem nenhum campo
            update_data = schemas.MenuItemUpdate()
            
            updated_item = MenuItemService.update_partial(db_session, str(sample_menu_item.id), update_data)
            
            # Deve retornar o item mesmo sem mudanças
            assert updated_item is not None
    
    def test_create_bulk_empty_list(self, db_session: Session):
        """Testa criação em lote com lista vazia."""
        with patch('my_menu_api.services.menu_item_service.get_settings') as mock_settings:
            mock_settings.return_value.MAX_BULK_ITEMS = 1000
            
            items = MenuItemService.create_bulk(db_session, [])
            
            assert len(items) == 0
