"""
Rotas da API para gerenciamento de itens do cardápio.
Camada de apresentação - responsável apenas por receber requisições e retornar respostas.
Inclui proteção por autenticação e autorização baseada em roles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request, UploadFile, File
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.menu_item_service import MenuItemService
from ..models import User
from ..auth import get_current_active_user, require_manager, require_admin


router = APIRouter(
    prefix="/menu-items",
    tags=["Menu Items"],
    responses={
        404: {"description": "Item não encontrado"},
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro interno do servidor"}
    }
)


@router.get("/", response_model=List[schemas.MenuItem], summary="Lista todos os itens do cardápio")
async def get_all_menu_items(db: Session = Depends(get_db)):
    """Retorna lista completa de itens do cardápio."""
    items = MenuItemService.get_all(db)
    return items


@router.get("/available", response_model=List[schemas.MenuItem], summary="Lista apenas itens disponíveis")
async def get_available_menu_items(db: Session = Depends(get_db)):
    """Retorna apenas itens marcados como disponíveis."""
    items = MenuItemService.get_available_items(db)
    return items


@router.get("/category/{category}", response_model=List[schemas.MenuItem], summary="Lista itens por categoria")
async def get_menu_items_by_category(category: str, db: Session = Depends(get_db)):
    """Retorna itens filtrados por categoria."""
    items = MenuItemService.get_by_category(db, category)
    return items


@router.get("/{item_id}", response_model=schemas.MenuItem, summary="Obtém item específico por ID")
async def get_menu_item_by_id(item_id: str, db: Session = Depends(get_db)):
    """Retorna detalhes de um item específico."""
    item = MenuItemService.get_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=404, 
            detail={
                "message": "Item de cardápio não encontrado", 
                "code": "ITEM_NOT_FOUND",
                "item_id": item_id
            }
        )
    return item


@router.post("/", response_model=schemas.MenuItem, status_code=status.HTTP_201_CREATED, summary="Cria novo item")
async def create_menu_item(
    item: schemas.MenuItemCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Cria um novo item do cardápio.
    Requer role Manager ou Admin.
    """
    try:
        return MenuItemService.create(db, item, current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Erro ao criar item",
                "error": str(e),
                "code": "CREATE_ERROR"
            }
        )


@router.post("/bulk", response_model=schemas.MenuItemBulkResponse, status_code=status.HTTP_201_CREATED, summary="Cria múltiplos itens")
async def create_menu_items_bulk(
    bulk_data: schemas.MenuItemBulkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Cria múltiplos itens em uma operação atômica.
    Requer role Manager ou Admin.
    """
    try:
        created_items = MenuItemService.create_bulk(db, bulk_data.items, current_user, request)
        # Converter objetos SQLAlchemy para objetos Pydantic
        pydantic_items = [schemas.MenuItem.model_validate(item) for item in created_items]
        return schemas.MenuItemBulkResponse(
            created_items=pydantic_items,
            total_created=len(created_items),
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "code": "VALIDATION_ERROR"})
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Erro ao criar itens em lote",
                "error": str(e),
                "code": "BULK_CREATE_ERROR"
            }
        )


@router.put("/{item_id}", response_model=schemas.MenuItem, summary="Atualização completa de item")
async def update_menu_item_full(
    item_id: str, 
    item: schemas.MenuItemCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Atualiza completamente um item (todos os campos obrigatórios).
    Requer role Manager ou Admin.
    """
    updated_item = MenuItemService.update_full(db, item_id, item)
    if not updated_item:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Item de cardápio não encontrado", 
                "code": "ITEM_NOT_FOUND",
                "item_id": item_id
            }
        )
    return updated_item


@router.patch("/{item_id}", response_model=schemas.MenuItem, summary="Atualização parcial de item")
async def update_menu_item_partial(
    item_id: str, 
    item_update: schemas.MenuItemUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Atualiza parcialmente um item (apenas campos fornecidos).
    Requer role Manager ou Admin.
    """
    updated_item = MenuItemService.update_partial(db, item_id, item_update)
    if not updated_item:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Item de cardápio não encontrado", 
                "code": "ITEM_NOT_FOUND",
                "item_id": item_id
            }
        )
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item do cardápio")
async def delete_menu_item(
    item_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Remove um item do cardápio permanentemente.
    Requer role Admin (operação crítica).
    """
    deleted = MenuItemService.delete(db, item_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Item de cardápio não encontrado", 
                "code": "ITEM_NOT_FOUND",
                "item_id": item_id
            }
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{item_id}/image", response_model=schemas.ImageUploadResponse)
async def upload_item_image(
    request: Request,
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Upload an image for a menu item"""
    try:
        from ..services.image_service import ImageService
        
        # Verificar se o item existe
        item = MenuItemService.get_menu_item(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Processar o upload da imagem
        image_service = ImageService()
        result = await image_service.process_image_upload(file, f"menu_item_{item_id}")
        
        # Atualizar o item com os dados da imagem
        item_update = schemas.MenuItemUpdate(
            image_filename=result["filename"],
            image_path=result["path"],
            image_url=result["url"]
        )
        
        updated_item = MenuItemService.update_menu_item(
            db, 
            item_id, 
            item_update, 
            current_user,
            str(request.client.host) if request.client else "unknown"
        )
        
        return schemas.ImageUploadResponse(
            filename=result["filename"],
            url=result["url"],
            sizes=result["sizes"],
            message="Image uploaded successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@router.delete("/{item_id}/image")
async def delete_item_image(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Remove the image from a menu item"""
    try:
        from ..services.image_service import ImageService
        from ..services.audit_service import model_to_dict, audit_update_simple
        
        # Verificar se o item existe
        item = MenuItemService.get_menu_item(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Salvar estado anterior para auditoria
        old_item_data = model_to_dict(item)
        
        # Deletar arquivos de imagem se existirem
        image_filename = getattr(item, 'image_filename', None)
        if image_filename:
            await ImageService.delete_image_files(image_filename)
        
        # Atualizar o item removendo os dados da imagem diretamente
        setattr(item, 'image_filename', None)
        setattr(item, 'image_path', None)
        setattr(item, 'image_url', None)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {"message": "Image deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
