"""
Serviço de Audit Log para rastreamento de mudanças.
Registra automaticamente todas as operações CRUD com contexto completo.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import Request

from ..models import AuditLog, User
from ..schemas import AuditLogCreate


class AuditService:
    """Serviço para gerenciamento de logs de auditoria."""
    
    @staticmethod
    def create_audit_log(
        db: Session,
        action: str,
        table_name: str,
        record_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Cria um registro de auditoria.
        
        Args:
            db: Sessão do banco de dados
            action: Ação realizada (CREATE, UPDATE, DELETE)
            table_name: Nome da tabela afetada
            record_id: ID do registro afetado
            old_values: Valores antigos (para UPDATE/DELETE)
            new_values: Valores novos (para CREATE/UPDATE)
            user: Usuário que realizou a ação
            request: Request HTTP para extrair contexto
        """
        
        # Preparar dados da mudança
        old_json = json.dumps(old_values, default=str) if old_values else None
        new_json = json.dumps(new_values, default=str) if new_values else None
        
        # Identificar campos alterados
        changed_fields = []
        if old_values and new_values:
            for key, new_value in new_values.items():
                old_value = old_values.get(key)
                if old_value != new_value:
                    changed_fields.append(key)
        
        changed_fields_json = json.dumps(changed_fields) if changed_fields else None
        
        # Extrair informações do request
        ip_address = None
        user_agent = None
        endpoint = None
        
        if request:
            # IP address (considerando proxies)
            ip_address = request.headers.get("X-Forwarded-For")
            if ip_address:
                ip_address = ip_address.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None
            
            # User agent
            user_agent = request.headers.get("User-Agent")
            
            # Endpoint
            endpoint = f"{request.method} {request.url.path}"
        
        # Criar registro de auditoria
        audit_log = AuditLog(
            id=uuid.uuid4(),
            action=action,
            table_name=table_name,
            record_id=str(record_id),
            old_values=old_json,
            new_values=new_json,
            changed_fields=changed_fields_json,
            user_id=user.id if user else None,
            username=user.username if user else None,
            user_role=user.role if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            created_at=datetime.now(timezone.utc)
        )
        
        try:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            return audit_log
        except Exception as e:
            db.rollback()
            # Em caso de erro no audit log, não queremos quebrar a operação principal
            print(f"Erro ao criar audit log: {e}")
            return None
    
    @staticmethod
    def log_create(
        db: Session,
        table_name: str,
        record_id: str,
        new_values: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """Registra criação de um registro."""
        return AuditService.create_audit_log(
            db=db,
            action="CREATE",
            table_name=table_name,
            record_id=record_id,
            new_values=new_values,
            user=user,
            request=request
        )
    
    @staticmethod
    def log_update(
        db: Session,
        table_name: str,
        record_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """Registra atualização de um registro."""
        return AuditService.create_audit_log(
            db=db,
            action="UPDATE",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            user=user,
            request=request
        )
    
    @staticmethod
    def log_delete(
        db: Session,
        table_name: str,
        record_id: str,
        old_values: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """Registra exclusão de um registro."""
        return AuditService.create_audit_log(
            db=db,
            action="DELETE",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            user=user,
            request=request
        )
    
    @staticmethod
    def get_audit_logs_for_record(
        db: Session,
        table_name: str,
        record_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Obtém histórico de auditoria para um registro específico."""
        return db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == str(record_id)
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_audit_logs_by_user(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Obtém histórico de auditoria de um usuário."""
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_recent_audit_logs(
        db: Session,
        limit: int = 100,
        table_name: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        """Obtém logs de auditoria recentes com filtros opcionais."""
        query = db.query(AuditLog)
        
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_audit_summary(db: Session, days: int = 30) -> Dict[str, Any]:
        """Gera resumo de atividades de auditoria."""
        from sqlalchemy import func, and_
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total de ações por tipo
        actions_summary = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= cutoff_date
        ).group_by(AuditLog.action).all()
        
        # Atividade por tabela
        tables_summary = db.query(
            AuditLog.table_name,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= cutoff_date
        ).group_by(AuditLog.table_name).all()
        
        # Usuários mais ativos
        users_summary = db.query(
            AuditLog.username,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.created_at >= cutoff_date,
                AuditLog.username.is_not(None)
            )
        ).group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        return {
            'period_days': days,
            'actions': {action: count for action, count in actions_summary},
            'tables': {table: count for table, count in tables_summary},
            'top_users': [{'username': username, 'actions': count} for username, count in users_summary],
            'total_actions': sum(count for _, count in actions_summary)
        }


def model_to_dict(instance, exclude_fields: List[str] = None) -> Dict[str, Any]:
    """
    Converte uma instância do SQLAlchemy em dicionário para auditoria.
    
    Args:
        instance: Instância do modelo SQLAlchemy
        exclude_fields: Campos a serem excluídos (ex: passwords, timestamps)
    """
    if exclude_fields is None:
        exclude_fields = ['hashed_password', 'password']
    
    result = {}
    for column in instance.__table__.columns:
        if column.name not in exclude_fields:
            value = getattr(instance, column.name)
            # Converter tipos especiais para string
            if isinstance(value, (datetime, uuid.UUID)):
                value = str(value)
            result[column.name] = value
    
    return result


def audit_create(db: Session, instance, user: Optional[User] = None, request: Optional[Request] = None):
    """Decorator/função para auditar criação."""
    new_values = model_to_dict(instance)
    AuditService.log_create(
        db=db,
        table_name=instance.__tablename__,
        record_id=str(instance.id),
        new_values=new_values,
        user=user,
        request=request
    )


def audit_update(db: Session, old_instance, new_instance, user: Optional[User] = None, request: Optional[Request] = None):
    """Decorator/função para auditar atualização."""
    # Se old_instance for um dict, usar diretamente
    if isinstance(old_instance, dict):
        old_values = old_instance
    else:
        old_values = model_to_dict(old_instance)
    
    new_values = model_to_dict(new_instance)
    
    AuditService.log_update(
        db=db,
        table_name=new_instance.__tablename__,
        record_id=str(new_instance.id),
        old_values=old_values,
        new_values=new_values,
        user=user,
        request=request
    )


def audit_update_simple(db: Session, old_values: Dict[str, Any], new_instance, user: Optional[User] = None, ip_address: Optional[str] = None):
    """Versão simplificada para auditar atualização com IP address."""
    new_values = model_to_dict(new_instance)
    
    # Simular um request simples se temos IP
    request_context = None
    if ip_address:
        class SimpleRequest:
            def __init__(self, ip: str):
                self.client = type('Client', (), {'host': ip})()
                self.headers = {}
                self.url = type('URL', (), {'path': f'/menu-items/{new_instance.id}'})()
        
        request_context = SimpleRequest(ip_address)
    
    AuditService.log_update(
        db=db,
        table_name=new_instance.__tablename__,
        record_id=str(new_instance.id),
        old_values=old_values,
        new_values=new_values,
        user=user,
        request=request_context
    )


def audit_delete(db: Session, instance, user: Optional[User] = None, request: Optional[Request] = None):
    """Decorator/função para auditar exclusão."""
    old_values = model_to_dict(instance)
    AuditService.log_delete(
        db=db,
        table_name=instance.__tablename__,
        record_id=str(instance.id),
        old_values=old_values,
        user=user,
        request=request
    )
