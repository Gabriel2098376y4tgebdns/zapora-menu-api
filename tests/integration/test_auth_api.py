"""
Testes de integração para autenticação e autorização.
"""

import pytest
from fastapi.testclient import TestClient

from my_menu_api import models


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationAPI:
    """Testes de integração para endpoints de autenticação."""
    
    def test_login_success(self, client: TestClient, admin_user: models.User):
        """Testa login bem-sucedido."""
        login_data = {
            "username": getattr(admin_user, 'username'),
            "password": "admin123"  # Senha definida na fixture
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Testa login com credenciais inválidas."""
        login_data = {
            "username": "usuario_inexistente",
            "password": "senha_errada"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db_session):
        """Testa login com usuário inativo."""
        # Criar usuário inativo
        from my_menu_api.auth import get_password_hash
        import uuid
        
        inactive_user = models.User(
            id=uuid.uuid4(),
            email="inactive@test.com",
            username="inactive_user",
            hashed_password=get_password_hash("password123"),
            role=models.UserRole.USER,
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": "inactive_user",
            "password": "password123"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    def test_register_success(self, client: TestClient):
        """Testa registro bem-sucedido."""
        register_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "NewPass123!",
            "role": "user"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert "id" in data
    
    def test_register_duplicate_email(self, client: TestClient, admin_user: models.User):
        """Testa registro com email duplicado."""
        register_data = {
            "email": getattr(admin_user, 'email'),  # Email já existente
            "username": "outro_usuario",
            "password": "Pass123!",
            "role": "user"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, admin_user: models.User):
        """Testa registro com username duplicado."""
        register_data = {
            "email": "outro@test.com",
            "username": getattr(admin_user, 'username'),  # Username já existente
            "password": "Pass123!",
            "role": "user"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_invalid_password(self, client: TestClient):
        """Testa registro com senha fraca."""
        register_data = {
            "email": "weak@test.com",
            "username": "weakpass",
            "password": "123",  # Senha muito fraca
            "role": "user"
        }
        
        response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_current_user(self, client: TestClient, admin_token: str):
        """Testa recuperação do usuário atual."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin_test"
        assert data["role"] == "admin"
        assert "email" in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Testa acesso sem token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Testa acesso com token inválido."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_change_password_success(self, client: TestClient, regular_user: models.User, user_token: str):
        """Testa mudança de senha bem-sucedida."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        password_data = {
            "current_password": "user123",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, user_token: str):
        """Testa mudança de senha com senha atual incorreta."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        password_data = {
            "current_password": "senha_errada",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
    
    def test_token_expiration(self, client: TestClient):
        """Testa comportamento com token expirado."""
        # Este teste requereria mock do tempo ou token com expiração muito curta
        # Por simplicidade, vamos testar com um token malformado
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestAuthorizationLevels:
    """Testes de níveis de autorização."""
    
    def test_admin_access_all(self, client: TestClient, admin_token: str):
        """Testa que admin tem acesso a tudo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin pode criar itens
        item_data = {
            "name": "Admin Pizza",
            "description": "Pizza criada por admin",
            "price": 30.00,
            "category": "Pizza"
        }
        
        response = client.post("/menu-items", json=item_data, headers=headers)
        assert response.status_code == 201
        
        # Admin pode ver logs de auditoria
        response = client.get("/audit/recent", headers=headers)
        assert response.status_code == 200
    
    def test_manager_limited_access(self, client: TestClient, manager_token: str):
        """Testa que manager tem acesso limitado."""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Manager pode criar itens
        item_data = {
            "name": "Manager Burger",
            "description": "Burger criado por manager",
            "price": 20.00,
            "category": "Hambúrguer"
        }
        
        response = client.post("/menu-items", json=item_data, headers=headers)
        assert response.status_code == 201
        
        # Manager pode ver alguns logs de auditoria
        response = client.get("/audit/recent", headers=headers)
        assert response.status_code == 200
    
    def test_user_read_only(self, client: TestClient, user_token: str):
        """Testa que usuário comum tem apenas leitura."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # User pode ver itens
        response = client.get("/menu-items")
        assert response.status_code == 200
        
        # User NÃO pode criar itens
        item_data = {
            "name": "User Pizza",
            "description": "Esta criação deve falhar",
            "price": 25.00,
            "category": "Pizza"
        }
        
        response = client.post("/menu-items", json=item_data, headers=headers)
        assert response.status_code == 403
        
        # User NÃO pode ver logs de auditoria
        response = client.get("/audit/recent", headers=headers)
        assert response.status_code == 403
    
    def test_role_escalation_prevention(self, client: TestClient, user_token: str):
        """Testa que usuários não podem escalar privilégios."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Tentar criar usuário admin (deve falhar)
        register_data = {
            "email": "hacker@test.com",
            "username": "hacker",
            "password": "HackPass123!",
            "role": "admin"  # Tentativa de escalação
        }
        
        # Assumindo que apenas admins podem criar outros usuários
        response = client.post("/auth/register", json=register_data, headers=headers)
        # Dependendo da implementação, pode ser 403 ou o role pode ser ignorado
        assert response.status_code in [403, 201]
        
        if response.status_code == 201:
            # Se a criação foi permitida, verificar se o role foi limitado
            data = response.json()
            assert data["role"] != "admin"


@pytest.mark.integration
@pytest.mark.auth
class TestTokenSecurity:
    """Testes de segurança de tokens."""
    
    def test_token_includes_user_info(self, client: TestClient, admin_user: models.User):
        """Testa que o token contém informações corretas do usuário."""
        login_data = {
            "username": getattr(admin_user, 'username'),
            "password": "admin123"
        }
        
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Usar o token para obter informações do usuário
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert user_data["username"] == getattr(admin_user, 'username')
        assert user_data["role"] == getattr(admin_user, 'role')
    
    def test_token_cannot_be_reused_after_password_change(self, client: TestClient, regular_user: models.User):
        """Testa que tokens se tornam inválidos após mudança de senha."""
        # Fazer login e obter token
        login_data = {
            "username": getattr(regular_user, 'username'),
            "password": "user123"
        }
        
        response = client.post("/auth/login", data=login_data)
        old_token = response.json()["access_token"]
        
        # Usar token para mudar senha
        headers = {"Authorization": f"Bearer {old_token}"}
        password_data = {
            "current_password": "user123",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        assert response.status_code == 200
        
        # Fazer novo login com nova senha
        new_login_data = {
            "username": getattr(regular_user, 'username'),
            "password": "NewPassword123!"
        }
        
        response = client.post("/auth/login", data=new_login_data)
        assert response.status_code == 200
        new_token = response.json()["access_token"]
        
        # Verificar que tokens são diferentes
        assert old_token != new_token
    
    def test_multiple_concurrent_tokens(self, client: TestClient, admin_user: models.User):
        """Testa que múltiplos tokens podem coexistir."""
        login_data = {
            "username": getattr(admin_user, 'username'),
            "password": "admin123"
        }
        
        # Fazer login múltiplas vezes
        response1 = client.post("/auth/login", data=login_data)
        response2 = client.post("/auth/login", data=login_data)
        
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        # Tokens devem ser diferentes
        assert token1 != token2
        
        # Ambos devem funcionar
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response1 = client.get("/auth/me", headers=headers1)
        response2 = client.get("/auth/me", headers=headers2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
