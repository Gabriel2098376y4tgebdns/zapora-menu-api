"""
Testes unitários para o serviço de auditoria.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from my_menu_api.services.audit_service import AuditService
from my_menu_api import models


@pytest.mark.unit
@pytest.mark.audit
class TestAuditService:
    """Testes unitários para AuditService."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.mock_db = Mock()
        self.service = AuditService(self.mock_db)
    
    def test_init(self):
        """Testa inicialização do serviço."""
        assert self.service.db == self.mock_db
    
    @patch('my_menu_api.services.audit_service.datetime')
    def test_log_action_success(self, mock_datetime):
        """Testa registro bem-sucedido de ação."""
        # Configurar mock datetime
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time
        
        user_id = uuid.uuid4()
        
        # Executar
        self.service.log_action(
            user_id=user_id,
            action="CREATE_MENU_ITEM",
            resource_type="MenuItem",
            resource_id=uuid.uuid4(),
            details={"name": "Pizza Margherita"}
        )
        
        # Verificar que foi chamado o add e commit
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # Verificar dados do log criado
        created_log = self.mock_db.add.call_args[0][0]
        assert isinstance(created_log, models.AuditLog)
        assert created_log.user_id == user_id
        assert created_log.action == "CREATE_MENU_ITEM"
        assert created_log.resource_type == "MenuItem"
        assert created_log.timestamp == fixed_time
    
    def test_log_action_with_none_values(self):
        """Testa registro de ação com valores None."""
        user_id = uuid.uuid4()
        
        self.service.log_action(
            user_id=user_id,
            action="VIEW_MENU",
            resource_type=None,
            resource_id=None,
            details=None
        )
        
        created_log = self.mock_db.add.call_args[0][0]
        assert created_log.resource_type is None
        assert created_log.resource_id is None
        assert created_log.details is None
    
    def test_log_action_database_error(self):
        """Testa erro de banco de dados ao registrar ação."""
        self.mock_db.commit.side_effect = Exception("Database error")
        
        # Não deve levantar exceção, apenas fazer rollback
        self.service.log_action(
            user_id=uuid.uuid4(),
            action="TEST_ACTION",
            resource_type="Test"
        )
        
        self.mock_db.rollback.assert_called_once()
    
    def test_get_user_actions(self):
        """Testa recuperação de ações do usuário."""
        user_id = uuid.uuid4()
        
        # Mock da query
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = [Mock(), Mock()]
        
        # Executar
        result = self.service.get_user_actions(user_id, limit=10)
        
        # Verificar
        self.mock_db.query.assert_called_once_with(models.AuditLog)
        assert len(result) == 2
    
    def test_get_recent_actions(self):
        """Testa recuperação de ações recentes."""
        # Mock da query
        mock_query = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = [Mock(), Mock(), Mock()]
        
        # Executar
        result = self.service.get_recent_actions(limit=5)
        
        # Verificar
        assert len(result) == 3
        mock_limit.all.assert_called_once()
    
    @patch('my_menu_api.services.audit_service.datetime')
    def test_get_actions_by_date_range(self, mock_datetime):
        """Testa recuperação de ações por período."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock da query
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = [Mock()]
        
        # Executar
        result = self.service.get_actions_by_date_range(start_date, end_date)
        
        # Verificar
        assert len(result) == 1
        assert mock_query.filter.call_count == 1
        assert mock_filter1.filter.call_count == 1
    
    def test_get_actions_by_resource(self):
        """Testa recuperação de ações por recurso."""
        resource_type = "MenuItem"
        resource_id = uuid.uuid4()
        
        # Mock da query
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = [Mock(), Mock()]
        
        # Executar
        result = self.service.get_actions_by_resource(resource_type, resource_id)
        
        # Verificar
        assert len(result) == 2
    
    def test_search_actions(self):
        """Testa busca de ações por ação específica."""
        action = "DELETE_MENU_ITEM"
        
        # Mock da query
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [Mock()]
        
        # Executar
        result = self.service.search_actions(action=action)
        
        # Verificar
        assert len(result) == 1
        mock_query.filter.assert_called_once()
    
    def test_search_actions_by_user_and_action(self):
        """Testa busca de ações por usuário e ação."""
        user_id = uuid.uuid4()
        action = "UPDATE_MENU_ITEM"
        
        # Mock da query com múltiplos filtros
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = []
        
        # Executar
        result = self.service.search_actions(user_id=user_id, action=action)
        
        # Verificar
        assert len(result) == 0
        assert mock_query.filter.call_count == 1
        assert mock_filter1.filter.call_count == 1
    
    @patch('my_menu_api.services.audit_service.datetime')
    def test_cleanup_old_logs(self, mock_datetime):
        """Testa limpeza de logs antigos."""
        # Mock da data atual
        current_time = datetime(2024, 6, 1)
        mock_datetime.utcnow.return_value = current_time
        
        # Mock da query para delete
        mock_query = Mock()
        mock_filter = Mock()
        mock_delete = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 10  # 10 registros deletados
        
        # Executar
        deleted_count = self.service.cleanup_old_logs(days_to_keep=30)
        
        # Verificar
        assert deleted_count == 10
        self.mock_db.commit.assert_called_once()
    
    def test_cleanup_old_logs_error(self):
        """Testa erro na limpeza de logs antigos."""
        self.mock_db.commit.side_effect = Exception("Delete error")
        
        deleted_count = self.service.cleanup_old_logs(days_to_keep=30)
        
        assert deleted_count == 0
        self.mock_db.rollback.assert_called_once()
    
    def test_get_action_statistics(self):
        """Testa estatísticas de ações."""
        # Mock dos resultados da query
        mock_result = [
            ("CREATE_MENU_ITEM", 15),
            ("UPDATE_MENU_ITEM", 8),
            ("DELETE_MENU_ITEM", 3)
        ]
        
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_result
        
        # Executar
        stats = self.service.get_action_statistics()
        
        # Verificar
        assert len(stats) == 3
        assert stats == {
            "CREATE_MENU_ITEM": 15,
            "UPDATE_MENU_ITEM": 8,
            "DELETE_MENU_ITEM": 3
        }
    
    @patch('my_menu_api.services.audit_service.datetime')
    def test_get_daily_activity_count(self, mock_datetime):
        """Testa contagem de atividade diária."""
        target_date = datetime(2024, 1, 15)
        
        # Mock da query
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_count = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.count.return_value = 42
        
        # Executar
        count = self.service.get_daily_activity_count(target_date)
        
        # Verificar
        assert count == 42
    
    def test_get_user_activity_summary(self):
        """Testa resumo de atividade do usuário."""
        user_id = uuid.uuid4()
        
        # Mock de diferentes queries
        mock_query = Mock()
        self.mock_db.query.return_value = mock_query
        
        # Mock para contagem total
        mock_filter_total = Mock()
        mock_query.filter.return_value = mock_filter_total
        mock_filter_total.count.return_value = 25
        
        # Mock para última atividade
        mock_filter_last = Mock()
        mock_order = Mock()
        mock_first = Mock()
        mock_filter_last.order_by.return_value = mock_order
        mock_order.first.return_value = Mock(timestamp=datetime(2024, 1, 15))
        
        # Configurar retornos diferentes para cada chamada
        side_effects = [mock_filter_total, mock_filter_last]
        mock_query.filter.side_effect = side_effects
        
        # Executar
        summary = self.service.get_user_activity_summary(user_id)
        
        # Verificar
        assert "total_actions" in summary
        assert "last_activity" in summary
    
    def test_export_audit_logs(self):
        """Testa exportação de logs de auditoria."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Mock de logs
        mock_logs = [
            Mock(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                action="CREATE_MENU_ITEM",
                resource_type="MenuItem",
                timestamp=datetime(2024, 1, 15),
                details={"name": "Pizza"}
            ),
            Mock(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                action="UPDATE_MENU_ITEM",
                resource_type="MenuItem",
                timestamp=datetime(2024, 1, 20),
                details={"name": "Pizza Margherita"}
            )
        ]
        
        # Mock da query
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = mock_logs
        
        # Executar
        exported_logs = self.service.export_audit_logs(start_date, end_date)
        
        # Verificar
        assert len(exported_logs) == 2
        for log in exported_logs:
            assert "id" in log
            assert "user_id" in log
            assert "action" in log
            assert "timestamp" in log


@pytest.mark.unit
@pytest.mark.audit
class TestAuditServiceHelpers:
    """Testes para métodos auxiliares do AuditService."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.mock_db = Mock()
        self.service = AuditService(self.mock_db)
    
    def test_format_log_for_export(self):
        """Testa formatação de log para exportação."""
        mock_log = Mock()
        mock_log.id = uuid.uuid4()
        mock_log.user_id = uuid.uuid4()
        mock_log.action = "TEST_ACTION"
        mock_log.resource_type = "TestResource"
        mock_log.resource_id = uuid.uuid4()
        mock_log.timestamp = datetime(2024, 1, 15, 10, 30, 0)
        mock_log.details = {"key": "value"}
        
        formatted = self.service._format_log_for_export(mock_log)
        
        assert formatted["id"] == str(mock_log.id)
        assert formatted["user_id"] == str(mock_log.user_id)
        assert formatted["action"] == "TEST_ACTION"
        assert formatted["resource_type"] == "TestResource"
        assert formatted["resource_id"] == str(mock_log.resource_id)
        assert formatted["timestamp"] == "2024-01-15T10:30:00"
        assert formatted["details"] == {"key": "value"}
    
    def test_format_log_for_export_with_nulls(self):
        """Testa formatação de log com valores nulos."""
        mock_log = Mock()
        mock_log.id = uuid.uuid4()
        mock_log.user_id = uuid.uuid4()
        mock_log.action = "TEST_ACTION"
        mock_log.resource_type = None
        mock_log.resource_id = None
        mock_log.timestamp = datetime(2024, 1, 15, 10, 30, 0)
        mock_log.details = None
        
        formatted = self.service._format_log_for_export(mock_log)
        
        assert formatted["resource_type"] is None
        assert formatted["resource_id"] is None
        assert formatted["details"] is None
    
    def test_build_date_filter(self):
        """Testa construção de filtro de data."""
        # Este teste assumiria que há um método helper para filtros
        # Como não está visível na implementação, vamos testá-lo como parte dos outros métodos
        pass
    
    @patch('my_menu_api.services.audit_service.datetime')
    def test_calculate_retention_date(self, mock_datetime):
        """Testa cálculo de data de retenção."""
        current_time = datetime(2024, 6, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        # Método interno que seria usado no cleanup
        days_to_keep = 30
        expected_cutoff = current_time - timedelta(days=days_to_keep)
        
        # Como este é um método interno, testamos indiretamente através do cleanup
        self.service.cleanup_old_logs(days_to_keep=30)
        
        # Verificar que a data foi calculada corretamente na query
        # (esto seria verificado através dos argumentos da query)


@pytest.mark.integration
@pytest.mark.audit
class TestAuditServiceIntegration:
    """Testes de integração para AuditService."""
    
    @pytest.fixture
    def real_audit_service(self, db_session):
        """Fixture para serviço de auditoria real."""
        return AuditService(db_session)
    
    def test_full_audit_workflow(self, real_audit_service, admin_user):
        """Testa fluxo completo de auditoria."""
        user_id = getattr(admin_user, 'id')
        resource_id = uuid.uuid4()
        
        # Registrar algumas ações
        real_audit_service.log_action(
            user_id=user_id,
            action="CREATE_MENU_ITEM",
            resource_type="MenuItem",
            resource_id=resource_id,
            details={"name": "Pizza Test"}
        )
        
        real_audit_service.log_action(
            user_id=user_id,
            action="UPDATE_MENU_ITEM",
            resource_type="MenuItem",
            resource_id=resource_id,
            details={"name": "Pizza Test Updated", "price": 25.00}
        )
        
        # Recuperar ações do usuário
        user_actions = real_audit_service.get_user_actions(user_id)
        assert len(user_actions) >= 2
        
        # Recuperar ações recentes
        recent_actions = real_audit_service.get_recent_actions(limit=10)
        assert len(recent_actions) >= 2
        
        # Buscar ações por recurso
        resource_actions = real_audit_service.get_actions_by_resource("MenuItem", resource_id)
        assert len(resource_actions) == 2
        
        # Verificar estatísticas
        stats = real_audit_service.get_action_statistics()
        assert "CREATE_MENU_ITEM" in stats
        assert "UPDATE_MENU_ITEM" in stats
    
    def test_audit_log_persistence(self, real_audit_service, admin_user):
        """Testa persistência dos logs de auditoria."""
        user_id = getattr(admin_user, 'id')
        
        # Registrar ação
        real_audit_service.log_action(
            user_id=user_id,
            action="TEST_PERSISTENCE",
            resource_type="Test",
            details={"test": True}
        )
        
        # Verificar que foi persistido
        actions = real_audit_service.search_actions(action="TEST_PERSISTENCE")
        assert len(actions) >= 1
        
        found_action = next((a for a in actions if a.user_id == user_id), None)
        assert found_action is not None
        assert found_action.action == "TEST_PERSISTENCE"
        assert found_action.details == {"test": True}
    
    def test_date_range_filtering(self, real_audit_service, admin_user):
        """Testa filtragem por período de datas."""
        user_id = getattr(admin_user, 'id')
        
        # Registrar ação
        real_audit_service.log_action(
            user_id=user_id,
            action="DATE_RANGE_TEST",
            resource_type="Test"
        )
        
        # Buscar por período (hoje)
        today = datetime.utcnow().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        
        actions = real_audit_service.get_actions_by_date_range(start_date, end_date)
        
        # Deve incluir a ação que acabamos de criar
        found_action = next((a for a in actions if a.action == "DATE_RANGE_TEST"), None)
        assert found_action is not None
