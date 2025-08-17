"""
Testes unitários para o serviço de imagens.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from pathlib import Path
import io
from PIL import Image

from my_menu_api.services.image_service import ImageService


@pytest.mark.unit
@pytest.mark.image
class TestImageService:
    """Testes unitários para ImageService."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.service = ImageService()
    
    def test_init_creates_upload_directory(self):
        """Testa que o diretório de upload é criado na inicialização."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            service = ImageService()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_generate_filename(self):
        """Testa geração de nomes de arquivo únicos."""
        filename1 = self.service.generate_filename("image.jpg")
        filename2 = self.service.generate_filename("image.jpg")
        
        # Filenames devem ser diferentes
        assert filename1 != filename2
        
        # Devem manter a extensão
        assert filename1.endswith(".jpg")
        assert filename2.endswith(".jpg")
        
        # Devem ser UUIDs válidos (parte antes da extensão)
        name_part = filename1.split('.')[0]
        try:
            uuid.UUID(name_part)
        except ValueError:
            pytest.fail("Nome do arquivo não é um UUID válido")
    
    def test_get_file_extension(self):
        """Testa extração de extensão de arquivo."""
        assert self.service.get_file_extension("image.jpg") == ".jpg"
        assert self.service.get_file_extension("photo.PNG") == ".png"
        assert self.service.get_file_extension("document.jpeg") == ".jpeg"
        assert self.service.get_file_extension("file") == ""
    
    def test_is_valid_image_format_valid(self):
        """Testa validação de formatos de imagem válidos."""
        valid_filenames = [
            "image.jpg", "photo.jpeg", "picture.png", 
            "image.JPG", "photo.PNG", "picture.JPEG"
        ]
        
        for filename in valid_filenames:
            assert self.service.is_valid_image_format(filename) is True
    
    def test_is_valid_image_format_invalid(self):
        """Testa validação de formatos de imagem inválidos."""
        invalid_filenames = [
            "document.pdf", "video.mp4", "audio.mp3",
            "text.txt", "archive.zip", "file_without_extension"
        ]
        
        for filename in invalid_filenames:
            assert self.service.is_valid_image_format(filename) is False
    
    @pytest.fixture
    def mock_image_file(self):
        """Fixture para arquivo de imagem mock."""
        file_mock = MagicMock()
        file_mock.filename = "test_image.jpg"
        file_mock.content_type = "image/jpeg"
        
        # Criar uma imagem real em bytes
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        file_mock.file = img_bytes
        file_mock.read.return_value = img_bytes.getvalue()
        
        return file_mock
    
    def test_validate_image_size_valid(self, mock_image_file):
        """Testa validação de tamanho de imagem válido."""
        # Configurar tamanho válido (menor que 5MB)
        mock_image_file.file.seek(0, 2)  # Ir para o final
        size = mock_image_file.file.tell()
        mock_image_file.file.seek(0)  # Voltar ao início
        
        # Como nossa imagem de teste é pequena, deve passar
        assert self.service.validate_image_size(mock_image_file) is True
    
    def test_validate_image_size_too_large(self):
        """Testa validação de imagem muito grande."""
        large_file_mock = MagicMock()
        large_file_mock.filename = "large_image.jpg"
        
        # Mock de arquivo grande (6MB)
        large_content = b"x" * (6 * 1024 * 1024)
        large_file_mock.file = io.BytesIO(large_content)
        
        assert self.service.validate_image_size(large_file_mock) is False
    
    def test_validate_image_content_valid(self, mock_image_file):
        """Testa validação de conteúdo de imagem válido."""
        mock_image_file.file.seek(0)
        assert self.service.validate_image_content(mock_image_file) is True
    
    def test_validate_image_content_invalid(self):
        """Testa validação de conteúdo de imagem inválido."""
        fake_file_mock = MagicMock()
        fake_file_mock.filename = "fake_image.jpg"
        fake_file_mock.file = io.BytesIO(b"This is not an image")
        
        assert self.service.validate_image_content(fake_file_mock) is False
    
    @patch('pathlib.Path.write_bytes')
    @patch('my_menu_api.services.image_service.ImageService.validate_image_content')
    @patch('my_menu_api.services.image_service.ImageService.validate_image_size')
    @patch('my_menu_api.services.image_service.ImageService.is_valid_image_format')
    async def test_save_image_success(self, mock_format, mock_size, mock_content, mock_write, mock_image_file):
        """Testa salvamento bem-sucedido de imagem."""
        # Configurar mocks para sucesso
        mock_format.return_value = True
        mock_size.return_value = True
        mock_content.return_value = True
        
        # Mock do conteúdo do arquivo
        mock_image_file.read.return_value = b"fake_image_content"
        
        result = await self.service.save_image(mock_image_file)
        
        assert result is not None
        assert result.endswith(".jpg")
        mock_write.assert_called_once()
    
    @patch('my_menu_api.services.image_service.ImageService.is_valid_image_format')
    async def test_save_image_invalid_format(self, mock_format, mock_image_file):
        """Testa falha ao salvar imagem com formato inválido."""
        mock_format.return_value = False
        
        with pytest.raises(ValueError, match="Formato de imagem não suportado"):
            await self.service.save_image(mock_image_file)
    
    @patch('my_menu_api.services.image_service.ImageService.is_valid_image_format')
    @patch('my_menu_api.services.image_service.ImageService.validate_image_size')
    async def test_save_image_too_large(self, mock_size, mock_format, mock_image_file):
        """Testa falha ao salvar imagem muito grande."""
        mock_format.return_value = True
        mock_size.return_value = False
        
        with pytest.raises(ValueError, match="Imagem muito grande"):
            await self.service.save_image(mock_image_file)
    
    @patch('my_menu_api.services.image_service.ImageService.is_valid_image_format')
    @patch('my_menu_api.services.image_service.ImageService.validate_image_size')
    @patch('my_menu_api.services.image_service.ImageService.validate_image_content')
    async def test_save_image_invalid_content(self, mock_content, mock_size, mock_format, mock_image_file):
        """Testa falha ao salvar imagem com conteúdo inválido."""
        mock_format.return_value = True
        mock_size.return_value = True
        mock_content.return_value = False
        
        with pytest.raises(ValueError, match="Arquivo não é uma imagem válida"):
            await self.service.save_image(mock_image_file)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_image_success(self, mock_unlink, mock_exists):
        """Testa remoção bem-sucedida de imagem."""
        mock_exists.return_value = True
        
        result = self.service.delete_image("test_image.jpg")
        
        assert result is True
        mock_unlink.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_delete_image_not_found(self, mock_exists):
        """Testa remoção de imagem que não existe."""
        mock_exists.return_value = False
        
        result = self.service.delete_image("non_existent.jpg")
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_image_error(self, mock_unlink, mock_exists):
        """Testa erro ao remover imagem."""
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError("Erro de permissão")
        
        result = self.service.delete_image("protected_image.jpg")
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    def test_get_image_path_exists(self, mock_exists):
        """Testa obtenção de caminho de imagem existente."""
        mock_exists.return_value = True
        
        path = self.service.get_image_path("existing_image.jpg")
        
        assert path is not None
        assert str(path).endswith("existing_image.jpg")
    
    @patch('pathlib.Path.exists')
    def test_get_image_path_not_exists(self, mock_exists):
        """Testa obtenção de caminho de imagem inexistente."""
        mock_exists.return_value = False
        
        path = self.service.get_image_path("non_existent.jpg")
        
        assert path is None
    
    def test_get_upload_directory(self):
        """Testa obtenção do diretório de upload."""
        upload_dir = self.service.get_upload_directory()
        
        assert upload_dir is not None
        assert isinstance(upload_dir, Path)
        assert str(upload_dir).endswith("uploads")
    
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.unlink')
    def test_cleanup_old_images(self, mock_unlink, mock_is_file, mock_iterdir):
        """Testa limpeza de imagens antigas."""
        # Mock de arquivos no diretório
        old_file1 = Mock()
        old_file1.name = "old_image1.jpg"
        old_file1.stat.return_value.st_mtime = 1000000  # Timestamp antigo
        
        old_file2 = Mock()
        old_file2.name = "old_image2.jpg"
        old_file2.stat.return_value.st_mtime = 1000000
        
        recent_file = Mock()
        recent_file.name = "recent_image.jpg"
        recent_file.stat.return_value.st_mtime = 9999999999  # Timestamp recente
        
        mock_iterdir.return_value = [old_file1, old_file2, recent_file]
        mock_is_file.return_value = True
        
        with patch('time.time', return_value=9999999999):
            deleted_count = self.service.cleanup_old_images(days_old=30)
        
        assert deleted_count == 2
        assert mock_unlink.call_count == 2
    
    @patch('my_menu_api.services.image_service.ImageService.delete_image')
    async def test_update_menu_item_image(self, mock_delete):
        """Testa atualização de imagem de item do menu."""
        mock_delete.return_value = True
        
        # Simular item com imagem antiga
        old_image = "old_image.jpg"
        new_image = "new_image.jpg"
        
        await self.service.update_menu_item_image(old_image, new_image)
        
        mock_delete.assert_called_once_with(old_image)
    
    def test_get_supported_formats(self):
        """Testa obtenção de formatos suportados."""
        formats = self.service.get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "jpg" in formats
        assert "png" in formats
        assert "jpeg" in formats
    
    def test_get_max_file_size(self):
        """Testa obtenção do tamanho máximo de arquivo."""
        max_size = self.service.get_max_file_size()
        
        assert isinstance(max_size, int)
        assert max_size > 0
        assert max_size == 5 * 1024 * 1024  # 5MB
    
    @patch('my_menu_api.services.image_service.ImageService.get_image_path')
    def test_image_exists(self, mock_get_path):
        """Testa verificação de existência de imagem."""
        # Imagem existe
        mock_get_path.return_value = Path("/fake/path/image.jpg")
        assert self.service.image_exists("image.jpg") is True
        
        # Imagem não existe
        mock_get_path.return_value = None
        assert self.service.image_exists("non_existent.jpg") is False
    
    def test_resize_image_for_thumbnail(self, mock_image_file):
        """Testa redimensionamento de imagem para thumbnail."""
        # Configurar imagem original
        original_img = Image.new('RGB', (800, 600), color='blue')
        img_bytes = io.BytesIO()
        original_img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        mock_image_file.file = img_bytes
        
        # Redimensionar
        thumbnail = self.service.resize_image_for_thumbnail(mock_image_file)
        
        assert thumbnail is not None
        # Verificar se as dimensões foram reduzidas
        img = Image.open(thumbnail)
        assert img.width <= 300
        assert img.height <= 300
    
    @patch('pathlib.Path.stat')
    def test_get_image_info(self, mock_stat):
        """Testa obtenção de informações da imagem."""
        # Mock do arquivo
        mock_stat.return_value.st_size = 1024 * 1024  # 1MB
        mock_stat.return_value.st_mtime = 1234567890
        
        with patch('pathlib.Path.exists', return_value=True):
            info = self.service.get_image_info("test_image.jpg")
        
        assert info is not None
        assert "size" in info
        assert "modified" in info
        assert "filename" in info
        assert info["filename"] == "test_image.jpg"
    
    @patch('pathlib.Path.exists')
    def test_get_image_info_not_found(self, mock_exists):
        """Testa obtenção de informações de imagem inexistente."""
        mock_exists.return_value = False
        
        info = self.service.get_image_info("non_existent.jpg")
        
        assert info is None


@pytest.mark.integration
@pytest.mark.image
class TestImageServiceIntegration:
    """Testes de integração para ImageService."""
    
    def test_full_image_workflow(self, tmp_path):
        """Testa fluxo completo de imagem."""
        # Configurar serviço com diretório temporário
        service = ImageService()
        service.upload_dir = tmp_path / "uploads"
        service.upload_dir.mkdir(exist_ok=True)
        
        # Criar imagem de teste
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Mock do arquivo
        mock_file = MagicMock()
        mock_file.filename = "test_integration.jpg"
        mock_file.file = img_bytes
        mock_file.read.return_value = img_bytes.getvalue()
        
        # Salvar imagem
        filename = service.save_image(mock_file)
        assert filename is not None
        
        # Verificar se arquivo foi criado
        file_path = service.get_image_path(filename)
        assert file_path is not None
        assert file_path.exists()
        
        # Verificar informações
        info = service.get_image_info(filename)
        assert info is not None
        assert info["size"] > 0
        
        # Deletar imagem
        assert service.delete_image(filename) is True
        assert not file_path.exists()
