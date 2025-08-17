
from sqlalchemy import Column, Float, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime, timezone 
from sqlalchemy.sql import func 
from .database import Base


class UserRole(str, enum.Enum):
    """Enum para definir os roles de usuário."""
    ADMIN = "admin"
    MANAGER = "manager" 
    USER = "user"

class GUID(TypeDecorator):
   
    impl = CHAR(36) # Armazenará o UUID como uma string de 36 caracteres no banco de dados
    cache_ok = True

    def load_dialect_impl(self, dialect):
        # Para SQLite e outros bancos que não possuem tipo nativo de UUID,
        # armazenamos como CHAR(36).
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
     
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            # Se o valor não for um objeto UUID, tenta converter para um antes de processar
            try:
                value = uuid.UUID(value)
            except ValueError:
                raise TypeError(f"Value must be a uuid.UUID object or convertible string, got {type(value)}")
        return str(value) # Retorna a representação string do UUID

    def process_result_value(self, value, dialect):
       
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value # Já é um UUID, retorna como está
        return uuid.UUID(value) # Converte a string para um objeto UUID

class MenuItem(Base):
    # Define o nome da tabela no banco de dados
    __tablename__ = "menu_items"

    # Define as colunas da tabela
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    category = Column(String, index=True)
    available = Column(Boolean, default=True)
    
    # Campos de imagem
    image_filename = Column(String, nullable=True)  # Nome do arquivo de imagem
    image_path = Column(String, nullable=True)      # Caminho relativo da imagem
    image_url = Column(String, nullable=True)       # URL da imagem (se hospedada externamente)

    created_at = Column(DateTime(timezone=True), default=func.now()) 
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()) 


    def __repr__(self):
        return f"<MenuItem(id='{self.id}', name='{self.name}', category='{self.category}')>"


class User(Base):
    """Modelo de usuário para autenticação e autorização."""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # Role do usuário
    role = Column(String, default=UserRole.USER.value, nullable=False)
    
    # Status da conta
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"
    
    def has_role(self, required_role: UserRole) -> bool:
        """Verifica se o usuário tem o role necessário."""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        user_level = role_hierarchy.get(UserRole(self.role), 0)
        required_level = role_hierarchy.get(required_role, 999)
        return user_level >= required_level


class AuditLog(Base):
    """Modelo para auditoria e histórico de mudanças."""
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    # Informações da ação
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String, nullable=False)  # Nome da tabela afetada
    record_id = Column(String, nullable=False)  # ID do registro afetado
    
    # Dados da mudança
    old_values = Column(Text, nullable=True)  # JSON com valores antigos
    new_values = Column(Text, nullable=True)  # JSON com valores novos
    changed_fields = Column(Text, nullable=True)  # Lista de campos alterados
    
    # Informações do usuário e contexto
    user_id = Column(GUID(), nullable=True)  # ID do usuário que fez a mudança
    username = Column(String, nullable=True)  # Username para facilitar consultas
    user_role = Column(String, nullable=True)  # Role do usuário no momento da ação
    
    # Informações técnicas
    ip_address = Column(String, nullable=True)  # IP do usuário
    user_agent = Column(String, nullable=True)  # User agent do browser
    endpoint = Column(String, nullable=True)  # Endpoint da API utilizado
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id='{self.id}', action='{self.action}', table='{self.table_name}', record='{self.record_id}')>"
