"""
Schemas Pydantic para validação de dados da API.
Utiliza Pydantic v2 com recursos aprimorados de validação e serialização.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
from datetime import datetime
from typing import Optional, List, Union, Dict, Any
from decimal import Decimal
from enum import Enum


# Enum para roles (para uso nos schemas)
class UserRole(str, Enum):
    """Enum para definir os roles de usuário."""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class MenuItemBase(BaseModel):
    """Schema base com campos comuns para MenuItem."""
    name: str = Field(..., min_length=1, max_length=100, description="Nome do item")
    description: Optional[str] = Field(None, max_length=500, description="Descrição do item")
    price: float = Field(..., gt=0, description="Preço do item (deve ser positivo)")
    category: str = Field(..., min_length=1, max_length=50, description="Categoria do item")
    available: bool = Field(True, description="Item disponível para venda")
    
    # Campos de imagem (opcionais)
    image_filename: Optional[str] = Field(None, description="Nome do arquivo de imagem")
    image_path: Optional[str] = Field(None, description="Caminho da imagem")
    image_url: Optional[str] = Field(None, description="URL da imagem")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Valida se o preço é um valor monetário válido."""
        if v <= 0:
            raise ValueError('Preço deve ser maior que zero')
        # Limita a 2 casas decimais
        return round(float(v), 2)

    @field_validator('name', 'category')
    @classmethod
    def validate_strings(cls, v):
        """Remove espaços extras e valida strings."""
        if v:
            return v.strip()
        return v


class MenuItemCreate(MenuItemBase):
    """Schema para criação de novos itens."""
    pass


class MenuItem(MenuItemBase):
    """Schema completo do MenuItem para retorno da API."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MenuItemUpdate(BaseModel):
    """Schema para atualização parcial de itens."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    available: Optional[bool] = None
    image_filename: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Valida preço se fornecido."""
        if v is not None and v <= 0:
            raise ValueError('Preço deve ser maior que zero')
        if v is not None:
            return round(float(v), 2)
        return v


class MenuItemBulkCreate(BaseModel):
    """Schema para criação em lote de itens."""
    items: List[MenuItemCreate] = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        description="Lista de itens para criação (máximo 1.000)"
    )


class MenuItemBulkResponse(BaseModel):
    """Schema de resposta para operações em lote."""
    created_items: List[MenuItem]
    total_created: int = Field(..., description="Número total de itens criados")
    success: bool = Field(True, description="Indica se a operação foi bem-sucedida")

    @field_validator('total_created')
    @classmethod
    def validate_count(cls, v: int) -> int:
        """Valida se o count é válido."""
        if v < 0:
            raise ValueError('total_created deve ser não-negativo')
        return v


# Schemas para respostas de erro padronizadas
class ErrorDetail(BaseModel):
    """Schema padronizado para detalhes de erro."""
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Schema padronizado para respostas de erro."""
    error: ErrorDetail
    timestamp: datetime
    path: Optional[str] = None


# ============================================================================
# SCHEMAS DE AUTENTICAÇÃO E USUÁRIOS
# ============================================================================

class UserBase(BaseModel):
    """Schema base para usuário."""
    email: EmailStr = Field(..., description="Email do usuário")
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário")
    full_name: Optional[str] = Field(None, max_length=100, description="Nome completo")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Valida o nome de usuário."""
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username deve conter apenas letras, números e underscore')
        return v.lower().strip()


class UserCreate(UserBase):
    """Schema para criação de usuário."""
    password: str = Field(..., min_length=8, description="Senha do usuário")
    role: UserRole = Field(UserRole.USER, description="Role do usuário")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida a força da senha."""
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v


class User(UserBase):
    """Schema completo do usuário para retorno."""
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema para atualização de usuário."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None


class UserLogin(BaseModel):
    """Schema para login de usuário."""
    username: str = Field(..., description="Username ou email")
    password: str = Field(..., description="Senha do usuário")


class Token(BaseModel):
    """Schema para token de acesso."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # em segundos


class TokenData(BaseModel):
    """Schema para dados do token."""
    username: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    role: Optional[UserRole] = None


class ChangePassword(BaseModel):
    """Schema para mudança de senha."""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, description="Nova senha")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Valida a nova senha."""
        if len(v) < 8:
            raise ValueError('Nova senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Nova senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Nova senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Nova senha deve conter pelo menos um número')
        return v


# ============================================================================
# SCHEMAS DE AUDIT LOG
# ============================================================================

class AuditLogBase(BaseModel):
    """Schema base para audit log."""
    action: str = Field(..., description="Ação realizada (CREATE, UPDATE, DELETE)")
    table_name: str = Field(..., description="Nome da tabela afetada")
    record_id: str = Field(..., description="ID do registro afetado")
    old_values: Optional[str] = Field(None, description="Valores antigos (JSON)")
    new_values: Optional[str] = Field(None, description="Valores novos (JSON)")
    changed_fields: Optional[str] = Field(None, description="Campos alterados")
    username: Optional[str] = Field(None, description="Username do usuário")
    user_role: Optional[str] = Field(None, description="Role do usuário")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    user_agent: Optional[str] = Field(None, description="User agent")
    endpoint: Optional[str] = Field(None, description="Endpoint da API")


class AuditLog(AuditLogBase):
    """Schema completo do audit log para retorno."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(AuditLogBase):
    """Schema para criação de audit log."""
    user_id: Optional[uuid.UUID] = None


# ============================================================================
# SCHEMAS DE UPLOAD DE IMAGEM
# ============================================================================

class ImageUploadResponse(BaseModel):
    """Schema de resposta para upload de imagem."""
    filename: str = Field(..., description="Nome do arquivo salvo")
    url: str = Field(..., description="URL da imagem")
    message: str = Field(..., description="Mensagem de sucesso")
    sizes: Dict[str, str] = Field(default_factory=dict, description="URLs das diferentes resoluções")
    path: Optional[str] = Field(None, description="Caminho da imagem")
    size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    content_type: Optional[str] = Field(None, description="Tipo de conteúdo")


class ImageDeleteResponse(BaseModel):
    """Schema de resposta para remoção de imagem."""
    message: str = Field(..., description="Mensagem de confirmação")
    deleted_files: List[str] = Field(..., description="Arquivos removidos")