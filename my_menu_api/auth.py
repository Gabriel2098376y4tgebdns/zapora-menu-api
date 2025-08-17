"""
Serviços de autenticação e autorização.
Implementa JWT, hash de senhas e verificação de permissões.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User, UserRole
from .schemas import TokenData, UserCreate


settings = get_settings()

# Configuração do contexto de hash de senha
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)

# Security scheme para JWT
security = HTTPBearer()


# ============================================================================
# FUNÇÕES DE HASH E VERIFICAÇÃO DE SENHA
# ============================================================================

def get_password_hash(password: str) -> str:
    """Gera o hash da senha."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# FUNÇÕES JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT de acesso."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verifica e decodifica um token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            return None
            
        token_data = TokenData(
            username=username,
            user_id=uuid.UUID(user_id) if user_id else None,
            role=UserRole(role) if role else None
        )
        return token_data
        
    except (JWTError, ValueError):
        return None


# ============================================================================
# FUNÇÕES DE USUÁRIO
# ============================================================================

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autentica um usuário com username/email e senha."""
    # Procura por username ou email
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    # Atualiza último login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Busca usuário por username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Busca usuário por ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_create: UserCreate) -> User:
    """Cria um novo usuário."""
    # Verifica se username já existe
    if get_user_by_username(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já está em uso"
        )
    
    # Verifica se email já existe
    if get_user_by_email(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Cria o usuário
    hashed_password = get_password_hash(user_create.password)
    
    db_user = User(
        id=uuid.uuid4(),
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        role=user_create.role.value,
        is_active=True,
        is_verified=False,  # Por padrão, usuários precisam verificar email
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


# ============================================================================
# DEPENDÊNCIAS DE AUTENTICAÇÃO
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtém o usuário atual a partir do token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        token_data = verify_token(token)
        
        if token_data is None or token_data.username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtém o usuário atual se estiver ativo."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user


# ============================================================================
# DEPENDÊNCIAS DE AUTORIZAÇÃO
# ============================================================================

def require_role(required_role: UserRole):
    """Factory function para criar dependências de autorização por role."""
    
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        """Verifica se o usuário tem o role necessário."""
        user_role = UserRole(current_user.role)
        
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer role: {required_role.value}"
            )
        
        return current_user
    
    return role_checker


# Dependências pré-configuradas para roles específicos
require_admin = require_role(UserRole.ADMIN)
require_manager = require_role(UserRole.MANAGER)
require_user = require_role(UserRole.USER)


# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def create_admin_user_if_not_exists(db: Session) -> None:
    """Cria usuário admin padrão se não existir."""
    admin_user = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
    
    if not admin_user:
        admin_data = UserCreate(
            email=settings.DEFAULT_ADMIN_EMAIL,
            username=settings.DEFAULT_ADMIN_USERNAME,
            password=settings.DEFAULT_ADMIN_PASSWORD,
            full_name="Administrador do Sistema",
            role=UserRole.ADMIN
        )
        
        create_user(db, admin_data)
        print(f"✅ Usuário admin criado: {settings.DEFAULT_ADMIN_USERNAME}")


def change_user_password(db: Session, user: User, new_password: str) -> bool:
    """Altera a senha do usuário."""
    try:
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
