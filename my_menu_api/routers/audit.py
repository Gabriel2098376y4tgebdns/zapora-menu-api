"""
Rotas para gerenciamento de audit logs.
Permite consultar histórico de mudanças e relatórios de auditoria.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..auth import get_current_active_user, require_manager, require_admin
from ..database import get_db
from ..models import User
from ..schemas import AuditLog as AuditLogSchema
from ..services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=List[AuditLogSchema])
async def get_recent_audit_logs(
    limit: int = Query(100, le=1000, description="Número máximo de logs (máx: 1000)"),
    table_name: Optional[str] = Query(None, description="Filtrar por tabela"),
    action: Optional[str] = Query(None, description="Filtrar por ação (CREATE, UPDATE, DELETE)"),
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Lista logs de auditoria recentes.
    Requer role Manager ou Admin.
    """
    try:
        logs = AuditService.get_recent_audit_logs(
            db=db,
            limit=limit,
            table_name=table_name,
            action=action
        )
        return logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar logs: {str(e)}"
        )


@router.get("/logs/record/{table_name}/{record_id}", response_model=List[AuditLogSchema])
async def get_audit_logs_for_record(
    table_name: str,
    record_id: str,
    limit: int = Query(50, le=200, description="Número máximo de logs"),
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Obtém histórico de auditoria para um registro específico.
    Requer role Manager ou Admin.
    """
    try:
        logs = AuditService.get_audit_logs_for_record(
            db=db,
            table_name=table_name,
            record_id=record_id,
            limit=limit
        )
        
        if not logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum log encontrado para este registro"
            )
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )


@router.get("/logs/user/{user_id}", response_model=List[AuditLogSchema])
async def get_audit_logs_by_user(
    user_id: str,
    limit: int = Query(100, le=500, description="Número máximo de logs"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtém histórico de auditoria de um usuário específico.
    Requer role Admin.
    """
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        
        logs = AuditService.get_audit_logs_by_user(
            db=db,
            user_id=user_uuid,
            limit=limit
        )
        
        return logs
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar logs do usuário: {str(e)}"
        )


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(30, ge=1, le=365, description="Período em dias (1-365)"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Gera resumo de atividades de auditoria.
    Requer role Admin.
    """
    try:
        summary = AuditService.get_audit_summary(db=db, days=days)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar resumo: {str(e)}"
        )


@router.get("/me", response_model=List[AuditLogSchema])
async def get_my_audit_logs(
    limit: int = Query(50, le=200, description="Número máximo de logs"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtém histórico de auditoria do usuário autenticado.
    """
    try:
        logs = AuditService.get_audit_logs_by_user(
            db=db,
            user_id=current_user.id,
            limit=limit
        )
        
        return logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar seus logs: {str(e)}"
        )


@router.get("/stats")
async def get_audit_stats(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Estatísticas rápidas de auditoria.
    Requer role Manager ou Admin.
    """
    try:
        from sqlalchemy import func
        from ..models import AuditLog
        from datetime import datetime, timedelta, timezone
        
        # Total de logs
        total_logs = db.query(func.count(AuditLog.id)).scalar()
        
        # Logs das últimas 24 horas
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_logs = db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= yesterday
        ).scalar()
        
        # Ações mais comuns
        top_actions = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).order_by(
            func.count(AuditLog.id).desc()
        ).limit(5).all()
        
        return {
            "total_logs": total_logs,
            "recent_logs_24h": recent_logs,
            "top_actions": [{"action": action, "count": count} for action, count in top_actions],
            "period": "last_24_hours"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar estatísticas: {str(e)}"
        )
