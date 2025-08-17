"""
Testes de integração para os endpoints da API de menu items.
"""

import uuid
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from my_menu_api import models


@pytest.mark.integration
@pytest.mark.api
class TestMenuItemsAPI:
    """Testes de integração para endpoints de menu items."""
    
    def test_get_all_menu_items(self, client: TestClient, multiple_menu_items):
        """Testa GET /menu-items."""
        response = client.get("/menu-items")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # De acordo com multiple_menu_items fixture
    
    def test_get_menu_item_by_id(self, client: TestClient, sample_menu_item: models.MenuItem):
        """Testa GET /menu-items/{id}."""
        response = client.get(f"/menu-items/{sample_menu_item.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_menu_item.id)
        assert data["name"] == getattr(sample_menu_item, 'name')
    
    def test_get_menu_item_not_found(self, client: TestClient):
        """Testa GET /menu-items/{id} quando item não existe."""
        non_existent_id = str(uuid.uuid4())
        response = client.get(f"/menu-items/{non_existent_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_menu_item_success(self, client: TestClient, manager_token: str):
        """Testa POST /menu-items com sucesso."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        item_data = {
            "name": "Nova Pizza",
            "description": "Pizza criada via API",
            "price": 28.90,
            "category": "Pizza",
            "available": True
        }
        
        response = client.post("/menu-items", json=item_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Nova Pizza"
        assert data["price"] == 28.90
        assert "id" in data
    
    def test_create_menu_item_unauthorized(self, client: TestClient):
        """Testa POST /menu-items sem autenticação."""
        item_data = {
            "name": "Pizza Não Autorizada",
            "description": "Esta criação deve falhar",
            "price": 20.00,
            "category": "Pizza"
        }
        
        response = client.post("/menu-items", json=item_data)
        
        assert response.status_code == 401
    
    def test_create_menu_item_forbidden(self, client: TestClient, user_token: str):
        """Testa POST /menu-items com usuário sem permissão."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        item_data = {
            "name": "Pizza Proibida",
            "description": "Usuário comum não pode criar",
            "price": 20.00,
            "category": "Pizza"
        }
        
        response = client.post("/menu-items", json=item_data, headers=headers)
        
        assert response.status_code == 403
    
    def test_create_menu_item_invalid_data(self, client: TestClient, manager_token: str):
        """Testa POST /menu-items com dados inválidos."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Preço negativo
        invalid_data = {
            "name": "Pizza Inválida",
            "description": "Preço negativo",
            "price": -10.00,
            "category": "Pizza"
        }
        
        response = client.post("/menu-items", json=invalid_data, headers=headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_menu_item_success(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str):
        """Testa PUT /menu-items/{id} com sucesso."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        update_data = {
            "name": "Pizza Atualizada",
            "description": "Descrição atualizada",
            "price": 35.00,
            "category": "Pizza",
            "available": False
        }
        
        response = client.put(f"/menu-items/{sample_menu_item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pizza Atualizada"
        assert data["price"] == 35.00
        assert data["available"] is False
    
    def test_partial_update_menu_item(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str):
        """Testa PATCH /menu-items/{id}."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Atualizar apenas o preço
        update_data = {"price": 30.00}
        
        response = client.patch(f"/menu-items/{sample_menu_item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 30.00
        # Outros campos devem permanecer inalterados
        assert data["name"] == getattr(sample_menu_item, 'name')
    
    def test_delete_menu_item_success(self, client: TestClient, sample_menu_item: models.MenuItem, admin_token: str):
        """Testa DELETE /menu-items/{id} com sucesso."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.delete(f"/menu-items/{sample_menu_item.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verificar que o item foi removido
        get_response = client.get(f"/menu-items/{sample_menu_item.id}")
        assert get_response.status_code == 404
    
    def test_delete_menu_item_forbidden(self, client: TestClient, sample_menu_item: models.MenuItem, user_token: str):
        """Testa DELETE /menu-items/{id} sem permissão."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.delete(f"/menu-items/{sample_menu_item.id}", headers=headers)
        
        assert response.status_code == 403
    
    def test_get_available_items(self, client: TestClient, multiple_menu_items):
        """Testa GET /menu-items/available."""
        response = client.get("/menu-items/available")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos os itens retornados devem estar disponíveis
        assert all(item["available"] for item in data)
    
    def test_get_items_by_category(self, client: TestClient, multiple_menu_items):
        """Testa GET /menu-items/category/{category}."""
        response = client.get("/menu-items/category/Pizza")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos os itens devem ser da categoria Pizza
        assert all(item["category"] == "Pizza" for item in data)
    
    def test_bulk_create_menu_items(self, client: TestClient, manager_token: str):
        """Testa POST /menu-items/bulk."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        bulk_data = {
            "items": [
                {
                    "name": "Bulk Item 1",
                    "description": "Primeiro item em lote",
                    "price": 15.00,
                    "category": "Bulk"
                },
                {
                    "name": "Bulk Item 2",
                    "description": "Segundo item em lote",
                    "price": 18.00,
                    "category": "Bulk"
                }
            ]
        }
        
        response = client.post("/menu-items/bulk", json=bulk_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["total_created"] == 2
        assert len(data["created_items"]) == 2
        assert data["success"] is True


@pytest.mark.integration
@pytest.mark.image
class TestMenuItemImageAPI:
    """Testes de integração para upload de imagens de menu items."""
    
    def test_upload_image_success(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str, sample_image_file):
        """Testa POST /menu-items/{id}/image com sucesso."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Ler o arquivo de imagem
        with open(sample_image_file, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            
            response = client.post(f"/menu-items/{sample_menu_item.id}/image", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "url" in data
        assert "message" in data
        assert data["message"] == "Image uploaded successfully"
    
    def test_upload_image_invalid_file(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str, invalid_image_file):
        """Testa upload com arquivo inválido."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        with open(invalid_image_file, "rb") as f:
            files = {"file": ("not_image.txt", f, "text/plain")}
            
            response = client.post(f"/menu-items/{sample_menu_item.id}/image", files=files, headers=headers)
        
        assert response.status_code == 400 or response.status_code == 422
    
    def test_upload_image_unauthorized(self, client: TestClient, sample_menu_item: models.MenuItem, sample_image_file):
        """Testa upload sem autenticação."""
        with open(sample_image_file, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            
            response = client.post(f"/menu-items/{sample_menu_item.id}/image", files=files)
        
        assert response.status_code == 401
    
    def test_upload_image_forbidden(self, client: TestClient, sample_menu_item: models.MenuItem, user_token: str, sample_image_file):
        """Testa upload sem permissão."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        with open(sample_image_file, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            
            response = client.post(f"/menu-items/{sample_menu_item.id}/image", files=files, headers=headers)
        
        assert response.status_code == 403
    
    def test_upload_image_item_not_found(self, client: TestClient, manager_token: str, sample_image_file):
        """Testa upload para item inexistente."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        non_existent_id = uuid.uuid4()
        
        with open(sample_image_file, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            
            response = client.post(f"/menu-items/{non_existent_id}/image", files=files, headers=headers)
        
        assert response.status_code == 404
    
    def test_delete_image_success(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str):
        """Testa DELETE /menu-items/{id}/image."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Primeiro, simular que o item tem uma imagem
        # (em um teste real, faríamos upload primeiro)
        response = client.delete(f"/menu-items/{sample_menu_item.id}/image", headers=headers)
        
        # Pode ser 200 (sucesso) ou 404 (item sem imagem)
        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.api
class TestHealthAndRoot:
    """Testes para endpoints básicos da aplicação."""
    
    def test_root_endpoint(self, client: TestClient):
        """Testa GET /."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_check(self, client: TestClient):
        """Testa GET /health."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data


@pytest.mark.integration
@pytest.mark.database
class TestMenuItemsPersistence:
    """Testes de persistência para menu items."""
    
    def test_create_and_retrieve(self, client: TestClient, manager_token: str):
        """Testa criação e recuperação de item."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Criar item
        item_data = {
            "name": "Pizza de Persistência",
            "description": "Teste de persistência",
            "price": 25.00,
            "category": "Pizza",
            "available": True
        }
        
        create_response = client.post("/menu-items", json=item_data, headers=headers)
        assert create_response.status_code == 201
        
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Recuperar item
        get_response = client.get(f"/menu-items/{item_id}")
        assert get_response.status_code == 200
        
        retrieved_item = get_response.json()
        assert retrieved_item["name"] == "Pizza de Persistência"
        assert retrieved_item["price"] == 25.00
    
    def test_update_and_verify(self, client: TestClient, sample_menu_item: models.MenuItem, manager_token: str):
        """Testa atualização e verificação de persistência."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Atualizar item
        update_data = {"name": "Nome Atualizado", "price": 40.00}
        
        update_response = client.patch(f"/menu-items/{sample_menu_item.id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # Verificar que mudanças persistiram
        get_response = client.get(f"/menu-items/{sample_menu_item.id}")
        assert get_response.status_code == 200
        
        updated_item = get_response.json()
        assert updated_item["name"] == "Nome Atualizado"
        assert updated_item["price"] == 40.00
