"""
Rotas para upload de imagens e gerenciamento de arquivos.
Suporta upload, redimensionamento automático e gerenciamento de imagens.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session

from ..auth import get_current_active_user, require_manager
from ..database import get_db
from ..models import User
from ..schemas import ImageUploadResponse, ImageDeleteResponse
from ..services.image_service import ImageService

router = APIRouter(prefix="/images", tags=["Upload de Imagens"])


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Upload de imagem com redimensionamento automático.
    Requer role Manager ou Admin.
    
    Gera automaticamente diferentes tamanhos:
    - original: Tamanho original (limitado)
    - large: 1200x800
    - medium: 800x600 (usado como principal)
    - small: 400x300
    - thumbnail: 150x150
    """
    try:
        result = await ImageService.process_image_upload(file)
        
        return ImageUploadResponse(
            filename=result['filename'],
            path=result['path'],
            url=result['url'],
            size=result['size'],
            content_type=result['content_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no upload: {str(e)}"
        )


@router.delete("/{filename}", response_model=ImageDeleteResponse)
async def delete_image(
    filename: str,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Remove uma imagem e todas suas versões redimensionadas.
    Requer role Manager ou Admin.
    """
    try:
        deleted_files = await ImageService.delete_image_files(filename)
        
        if not deleted_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Imagem não encontrada"
            )
        
        return ImageDeleteResponse(
            message=f"Imagem {filename} removida com sucesso",
            deleted_files=deleted_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover imagem: {str(e)}"
        )


@router.get("/{filename}/info")
async def get_image_info(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém informações sobre uma imagem.
    """
    info = ImageService.get_image_info(filename)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada"
        )
    
    return info


@router.get("/")
async def list_uploaded_images(
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todas as imagens uploadadas.
    """
    from pathlib import Path
    from ..services.image_service import IMAGES_DIR
    
    try:
        images = []
        if IMAGES_DIR.exists():
            for image_file in IMAGES_DIR.glob("*.{jpg,jpeg,png,webp,gif}"):
                if image_file.is_file():
                    info = ImageService.get_image_info(image_file.name)
                    if info:
                        images.append(info)
        
        return {
            "total": len(images),
            "images": images
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar imagens: {str(e)}"
        )
