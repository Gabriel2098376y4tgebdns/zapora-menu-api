"""
Serviços de lógica de negócio para MenuItem.
Centraliza todas as operações CRUD e regras de negócio com auditoria.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Request

from .. import models, schemas
from ..config import get_settings
from ..services.audit_service import audit_create, audit_update_simple, audit_delete, model_to_dict

settings = get_settings()


class MenuItemService:
    """Serviço responsável por todas as operações relacionadas a MenuItem."""
    
    @staticmethod
    def get_all(db: Session) -> List[models.MenuItem]:
        """Retorna todos os itens do cardápio."""
        return db.query(models.MenuItem).all()
    
    @staticmethod
    def get_by_id(db: Session, item_id: str) -> Optional[models.MenuItem]:
        """Busca um item específico por ID."""
        return db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    
    @staticmethod
    def get_menu_item(db: Session, item_id: int) -> Optional[models.MenuItem]:
        """Alias para get_by_id usando item_id como int."""
        return db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()
    
    @staticmethod
    def create(
        db: Session, 
        item_data: schemas.MenuItemCreate,
        user: Optional[models.User] = None,
        request: Optional[Request] = None
    ) -> models.MenuItem:
        """Cria um novo item do cardápio com auditoria."""
        db_item = models.MenuItem(**item_data.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Registrar auditoria
        audit_create(db, db_item, user, request)
        
        return db_item
    
    @staticmethod
    def create_bulk(
        db: Session, 
        items_data: List[schemas.MenuItemCreate],
        user: Optional[models.User] = None,
        request: Optional[Request] = None
    ) -> List[models.MenuItem]:
        """
        Cria múltiplos itens em uma transação atômica com auditoria.
        Otimizado para performance com bulk operations.
        """
        if len(items_data) > settings.MAX_BULK_ITEMS:
            raise ValueError(f"Máximo de {settings.MAX_BULK_ITEMS} itens permitidos por operação")
        
        try:
            created_items = []
            
            # Preparar todos os itens para inserção
            for item_data in items_data:
                db_item = models.MenuItem(**item_data.model_dump())
                db.add(db_item)
                created_items.append(db_item)
            
            # Commit uma única vez para toda a operação
            db.commit()
            
            # Refresh necessário apenas se precisarmos dos dados atualizados imediatamente
            # Em bulk operations, podemos otimizar isso
            return created_items
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e
    
    @staticmethod
    def update_full(db: Session, item_id: str, item_data: schemas.MenuItemCreate) -> Optional[models.MenuItem]:
        """Atualização completa de um item (PUT)."""
        db_item = MenuItemService.get_by_id(db, item_id)
        if not db_item:
            return None
        
        # Atualizar todos os campos
        for key, value in item_data.model_dump().items():
            setattr(db_item, key, value)
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def update_partial(db: Session, item_id: str, item_update: schemas.MenuItemUpdate) -> Optional[models.MenuItem]:
        """Atualização parcial de um item (PATCH)."""
        db_item = MenuItemService.get_by_id(db, item_id)
        if not db_item:
            return None
        
        # Atualizar apenas campos fornecidos
        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def update_menu_item(
        db: Session, 
        item_id: int, 
        item_update: schemas.MenuItemUpdate,
        user: Optional[models.User] = None,
        ip_address: Optional[str] = None
    ) -> Optional[models.MenuItem]:
        """Atualiza um item com auditoria completa."""
        db_item = MenuItemService.get_menu_item(db, item_id)
        if not db_item:
            return None
        
        # Salvar estado anterior para auditoria
        old_item_data = model_to_dict(db_item)
        
        # Atualizar apenas campos fornecidos
        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Registrar auditoria
        audit_update_simple(db, old_item_data, db_item, user, ip_address)
        
        return db_item
    
    @staticmethod
    def delete(db: Session, item_id: str) -> bool:
        """Remove um item do cardápio."""
        db_item = MenuItemService.get_by_id(db, item_id)
        if not db_item:
            return False
        
        db.delete(db_item)
        db.commit()
        return True
    
    @staticmethod
    def get_by_category(db: Session, category: str) -> List[models.MenuItem]:
        """Busca itens por categoria."""
        return db.query(models.MenuItem).filter(models.MenuItem.category == category).all()
    
    @staticmethod
    def get_available_items(db: Session) -> List[models.MenuItem]:
        """Retorna apenas itens disponíveis."""
        return db.query(models.MenuItem).filter(models.MenuItem.available == True).all()
