"""
Rotas de autenticação e gerenciamento de usuários.
Inclui login, registro, e operações protegidas por role.
"""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    get_current_user,
    change_user_password,
    require_admin,
    require_manager,
    get_user_by_id
)
from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    Token,
    ChangePassword,
    UserRole
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["autenticação"])


# ============================================================================
# ROTAS DE AUTENTICAÇÃO
# ============================================================================

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário no sistema.
    
    - **email**: Email válido do usuário
    - **username**: Nome de usuário único (3-50 caracteres)
    - **password**: Senha forte (mínimo 8 caracteres)
    - **full_name**: Nome completo (opcional)
    - **role**: Role do usuário (padrão: USER)
    """
    try:
        db_user = create_user(db, user_create)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário e retorna token de acesso.
    
    - **username**: Username ou email do usuário
    - **password**: Senha do usuário
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta inativa"
        )
    
    # Cria o token de acesso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {
        "sub": user.username,
        "user_id": str(user.id),
        "role": user.role
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # em segundos
    }


# ============================================================================
# ROTAS DE PERFIL DE USUÁRIO
# ============================================================================

@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém o perfil do usuário autenticado.
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza o perfil do usuário autenticado.
    Usuários comuns só podem alterar dados pessoais.
    """
    # Remove campos que usuário comum não pode alterar
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Apenas admins podem alterar role, is_active, is_verified
    if current_user.role != UserRole.ADMIN.value:
        forbidden_fields = ['role', 'is_active', 'is_verified']
        for field in forbidden_fields:
            update_data.pop(field, None)
    
    # Atualiza os campos permitidos
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar perfil"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Altera a senha do usuário autenticado.
    """
    from ..auth import verify_password
    
    # Verifica senha atual
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Altera a senha
    if change_user_password(db, current_user, password_data.new_password):
        return {"message": "Senha alterada com sucesso"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao alterar senha"
        )


# ============================================================================
# ROTAS ADMINISTRATIVAS (REQUER ROLE ADMIN/MANAGER)
# ============================================================================

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Lista todos os usuários (requer role Manager ou Admin).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user_by_id_route(
    user_id: str,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Obtém usuário por ID (requer role Manager ou Admin).
    """
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )


@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user_by_admin(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Atualiza usuário por ID (requer role Admin).
    """
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Atualiza os campos fornecidos
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar usuário"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Desativa usuário por ID (requer role Admin).
    Não remove do banco, apenas marca como inativo.
    """
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Não permite deletar a si mesmo
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível desativar sua própria conta"
            )
        
        user.is_active = False
        db.commit()
        
        return {"message": f"Usuário {user.username} desativado com sucesso"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao desativar usuário"
        )


# ============================================================================
# ROTAS DE INFORMAÇÃO
# ============================================================================

@router.get("/roles")
async def get_available_roles():
    """
    Lista os roles disponíveis no sistema.
    """
    return {
        "roles": [role.value for role in UserRole],
        "descriptions": {
            UserRole.USER.value: "Usuário comum - acesso básico",
            UserRole.MANAGER.value: "Gerente - pode visualizar relatórios e gerenciar itens",
            UserRole.ADMIN.value: "Administrador - acesso total ao sistema"
        }
    }


@router.get("/protected-test")
async def protected_route_test(
    current_user: User = Depends(get_current_active_user)
):
    """
    Rota de teste para verificar autenticação.
    """
    return {
        "message": "Acesso autorizado!",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }
    }
