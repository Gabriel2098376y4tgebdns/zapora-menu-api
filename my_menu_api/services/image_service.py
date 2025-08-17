"""
Serviço de upload e gerenciamento de imagens.
Suporta redimensionamento, validação e otimização de imagens.
"""

import os
import uuid
import aiofiles
from typing import List, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException, status

from ..config import get_settings

settings = get_settings()

# Configurações de imagem
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = Path("uploads")
IMAGES_DIR = UPLOAD_DIR / "images"
THUMBNAILS_DIR = IMAGES_DIR / "thumbnails"

# Tamanhos de imagem
IMAGE_SIZES = {
    'original': None,  # Mantém tamanho original (com limite)
    'large': (1200, 800),
    'medium': (800, 600),
    'small': (400, 300),
    'thumbnail': (150, 150)
}

class ImageService:
    """Serviço para gerenciamento de imagens."""
    
    @staticmethod
    def create_directories():
        """Cria os diretórios necessários para upload."""
        UPLOAD_DIR.mkdir(exist_ok=True)
        IMAGES_DIR.mkdir(exist_ok=True)
        THUMBNAILS_DIR.mkdir(exist_ok=True)
        
        for size_name in IMAGE_SIZES.keys():
            if size_name != 'original':
                (IMAGES_DIR / size_name).mkdir(exist_ok=True)
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """Valida se o arquivo é uma imagem válida."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo é obrigatório"
            )
        
        # Verifica extensão
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Verifica tipo de conteúdo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo deve ser uma imagem"
            )
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Gera um nome único para o arquivo."""
        file_ext = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{file_ext}"
        return unique_name
    
    @staticmethod
    async def save_image_file(file: UploadFile, filename: str) -> str:
        """Salva o arquivo de imagem no disco."""
        file_path = IMAGES_DIR / filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                
                # Verifica tamanho do arquivo
                if len(content) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                
                await f.write(content)
            
            return str(file_path)
            
        except Exception as e:
            if file_path.exists():
                file_path.unlink()  # Remove arquivo se houve erro
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar arquivo: {str(e)}"
            )
    
    @staticmethod
    def resize_image(input_path: str, output_path: str, size: Tuple[int, int], quality: int = 85):
        """Redimensiona uma imagem mantendo a proporção."""
        try:
            with Image.open(input_path) as img:
                # Corrige orientação baseada em EXIF
                img = ImageOps.exif_transpose(img)
                
                # Converte para RGB se necessário (para JPEG)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Redimensiona mantendo proporção
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Salva com qualidade otimizada
                img.save(output_path, optimize=True, quality=quality)
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao redimensionar imagem: {str(e)}"
            )
    
    @staticmethod
    async def process_image_upload(file: UploadFile) -> dict:
        """Processa upload completo de imagem com redimensionamento."""
        # Criar diretórios
        ImageService.create_directories()
        
        # Validar arquivo
        ImageService.validate_image_file(file)
        
        # Gerar nome único
        filename = ImageService.generate_unique_filename(file.filename)
        base_name = Path(filename).stem
        file_ext = Path(filename).suffix
        
        try:
            # Salvar arquivo original
            original_path = await ImageService.save_image_file(file, filename)
            
            # Gerar diferentes tamanhos
            generated_files = {
                'original': {
                    'path': original_path,
                    'url': f"/static/images/{filename}",
                    'size': 'original'
                }
            }
            
            # Criar versões redimensionadas
            for size_name, dimensions in IMAGE_SIZES.items():
                if size_name == 'original' or dimensions is None:
                    continue
                
                # Caminho para versão redimensionada
                resized_dir = IMAGES_DIR / size_name
                resized_filename = f"{base_name}_{size_name}{file_ext}"
                resized_path = resized_dir / resized_filename
                
                # Redimensionar
                ImageService.resize_image(original_path, str(resized_path), dimensions)
                
                generated_files[size_name] = {
                    'path': str(resized_path),
                    'url': f"/static/images/{size_name}/{resized_filename}",
                    'size': size_name
                }
            
            # Retornar informações do upload
            file_size = Path(original_path).stat().st_size
            
            return {
                'filename': filename,
                'original_filename': file.filename,
                'path': f"images/{filename}",
                'url': generated_files['medium']['url'],  # URL principal (tamanho médio)
                'urls': generated_files,
                'size': file_size,
                'content_type': file.content_type
            }
            
        except Exception as e:
            # Limpar arquivos em caso de erro
            await ImageService.cleanup_failed_upload(base_name, file_ext)
            raise e
    
    @staticmethod
    async def cleanup_failed_upload(base_name: str, file_ext: str):
        """Remove arquivos de upload que falharam."""
        try:
            # Remove arquivo original
            original_file = IMAGES_DIR / f"{base_name}{file_ext}"
            if original_file.exists():
                original_file.unlink()
            
            # Remove versões redimensionadas
            for size_name in IMAGE_SIZES.keys():
                if size_name == 'original':
                    continue
                
                resized_file = IMAGES_DIR / size_name / f"{base_name}_{size_name}{file_ext}"
                if resized_file.exists():
                    resized_file.unlink()
                    
        except Exception:
            pass  # Ignora erros de limpeza
    
    @staticmethod
    async def delete_image_files(filename: str) -> List[str]:
        """Remove todos os arquivos relacionados a uma imagem."""
        if not filename:
            return []
        
        base_name = Path(filename).stem
        file_ext = Path(filename).suffix
        deleted_files = []
        
        try:
            # Remove arquivo original
            original_file = IMAGES_DIR / filename
            if original_file.exists():
                original_file.unlink()
                deleted_files.append(str(original_file))
            
            # Remove versões redimensionadas
            for size_name in IMAGE_SIZES.keys():
                if size_name == 'original':
                    continue
                
                resized_file = IMAGES_DIR / size_name / f"{base_name}_{size_name}{file_ext}"
                if resized_file.exists():
                    resized_file.unlink()
                    deleted_files.append(str(resized_file))
            
            return deleted_files
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao remover imagens: {str(e)}"
            )
    
    @staticmethod
    def get_image_info(filename: str) -> Optional[dict]:
        """Obtém informações sobre uma imagem."""
        if not filename:
            return None
        
        original_file = IMAGES_DIR / filename
        if not original_file.exists():
            return None
        
        try:
            with Image.open(original_file) as img:
                return {
                    'filename': filename,
                    'size': original_file.stat().st_size,
                    'dimensions': img.size,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception:
            return None
