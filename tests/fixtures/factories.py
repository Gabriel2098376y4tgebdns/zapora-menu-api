"""
Factories para geração de dados de teste usando Factory Boy.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import factory
import factory.fuzzy
from faker import Faker

from my_menu_api import models
from my_menu_api.auth import get_password_hash

fake = Faker('pt_BR')


class UserFactory(factory.Factory):
    """Factory para criar usuários de teste."""
    
    class Meta:
        model = models.User
    
    id = factory.LazyFunction(uuid.uuid4)
    email = factory.LazyAttribute(lambda obj: fake.email())
    username = factory.LazyAttribute(lambda obj: fake.user_name())
    hashed_password = factory.LazyAttribute(lambda obj: get_password_hash("password123"))
    role = factory.fuzzy.FuzzyChoice([models.UserRole.USER, models.UserRole.MANAGER, models.UserRole.ADMIN])
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class AdminUserFactory(UserFactory):
    """Factory específica para usuários admin."""
    
    role = models.UserRole.ADMIN
    email = "admin@test.com"
    username = "admin_test"


class ManagerUserFactory(UserFactory):
    """Factory específica para usuários manager."""
    
    role = models.UserRole.MANAGER
    email = "manager@test.com"
    username = "manager_test"


class RegularUserFactory(UserFactory):
    """Factory específica para usuários regulares."""
    
    role = models.UserRole.USER
    email = "user@test.com"
    username = "user_test"


class MenuItemFactory(factory.Factory):
    """Factory para criar itens de menu de teste."""
    
    class Meta:
        model = models.MenuItem
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyAttribute(lambda obj: fake.sentence(nb_words=3).rstrip('.'))
    description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    price = factory.fuzzy.FuzzyDecimal(5.0, 50.0, precision=2)
    category = factory.fuzzy.FuzzyChoice([
        "Pizza", "Hambúrguer", "Salada", "Bebida", "Sobremesa", 
        "Prato Principal", "Entrada", "Sanduíche"
    ])
    available = factory.fuzzy.FuzzyChoice([True, True, True, False])  # 75% disponível
    image_filename = None
    image_path = None
    image_url = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class PizzaItemFactory(MenuItemFactory):
    """Factory específica para pizzas."""
    
    name = factory.LazyAttribute(lambda obj: f"Pizza {fake.word().title()}")
    category = "Pizza"
    price = factory.fuzzy.FuzzyDecimal(20.0, 45.0, precision=2)
    description = factory.LazyAttribute(
        lambda obj: f"Pizza {fake.sentence(nb_words=8).rstrip('.')}"
    )


class BeverageItemFactory(MenuItemFactory):
    """Factory específica para bebidas."""
    
    name = factory.LazyAttribute(lambda obj: f"{fake.word().title()} {fake.random_element(['350ml', '500ml', '1L'])}")
    category = "Bebida"
    price = factory.fuzzy.FuzzyDecimal(3.0, 15.0, precision=2)
    description = factory.LazyAttribute(
        lambda obj: f"Bebida {fake.sentence(nb_words=5).rstrip('.')}"
    )


class AuditLogFactory(factory.Factory):
    """Factory para criar logs de auditoria de teste."""
    
    class Meta:
        model = models.AuditLog
    
    id = factory.LazyFunction(uuid.uuid4)
    action = factory.fuzzy.FuzzyChoice(["CREATE", "UPDATE", "DELETE"])
    table_name = factory.fuzzy.FuzzyChoice(["menu_items", "users"])
    record_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    old_values = factory.LazyAttribute(
        lambda obj: '{"name": "Old Value", "price": 10.00}' if obj.action != "CREATE" else None
    )
    new_values = factory.LazyAttribute(
        lambda obj: '{"name": "New Value", "price": 15.00}' if obj.action != "DELETE" else None
    )
    changed_fields = factory.LazyAttribute(
        lambda obj: '["name", "price"]' if obj.action == "UPDATE" else None
    )
    user_id = factory.LazyFunction(uuid.uuid4)
    username = factory.LazyAttribute(lambda obj: fake.user_name())
    user_role = factory.fuzzy.FuzzyChoice(["admin", "manager", "user"])
    ip_address = factory.LazyAttribute(lambda obj: fake.ipv4())
    user_agent = factory.LazyAttribute(lambda obj: fake.user_agent())
    endpoint = factory.fuzzy.FuzzyChoice(["/menu-items", "/users", "/auth/login"])
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


# ============================================================================
# FUNÇÕES AUXILIARES PARA CRIAÇÃO EM LOTE
# ============================================================================

def create_menu_items_batch(session, count: int = 10) -> list[models.MenuItem]:
    """Cria múltiplos itens de menu de uma vez."""
    items = []
    for _ in range(count):
        item = MenuItemFactory()
        session.add(item)
        items.append(item)
    
    session.commit()
    for item in items:
        session.refresh(item)
    
    return items


def create_users_batch(session, count: int = 5) -> list[models.User]:
    """Cria múltiplos usuários de uma vez."""
    users = []
    for i in range(count):
        # Garantir usernames únicos
        user = UserFactory(
            username=f"user_test_{i}",
            email=f"user{i}@test.com"
        )
        session.add(user)
        users.append(user)
    
    session.commit()
    for user in users:
        session.refresh(user)
    
    return users


def create_audit_logs_batch(session, count: int = 20) -> list[models.AuditLog]:
    """Cria múltiplos logs de auditoria de uma vez."""
    logs = []
    for _ in range(count):
        log = AuditLogFactory()
        session.add(log)
        logs.append(log)
    
    session.commit()
    for log in logs:
        session.refresh(log)
    
    return logs


# ============================================================================
# DADOS DE TESTE ESPECÍFICOS
# ============================================================================

SAMPLE_MENU_ITEMS = [
    {
        "name": "Pizza Margherita",
        "description": "Pizza clássica com molho de tomate, mozzarella e manjericão fresco",
        "price": 25.90,
        "category": "Pizza",
        "available": True
    },
    {
        "name": "Hambúrguer Bacon",
        "description": "Hambúrguer artesanal com bacon crocante, queijo cheddar e molho especial",
        "price": 22.50,
        "category": "Hambúrguer",
        "available": True
    },
    {
        "name": "Salada Caesar",
        "description": "Salada com alface romana, croutons, parmesão e molho caesar",
        "price": 18.00,
        "category": "Salada",
        "available": True
    },
    {
        "name": "Coca-Cola 350ml",
        "description": "Refrigerante Coca-Cola gelado",
        "price": 5.00,
        "category": "Bebida",
        "available": True
    },
    {
        "name": "Brownie com Sorvete",
        "description": "Brownie de chocolate com sorvete de baunilha e calda quente",
        "price": 12.90,
        "category": "Sobremesa",
        "available": False  # Temporariamente indisponível
    }
]

SAMPLE_USERS = [
    {
        "username": "admin_system",
        "email": "admin@menuapi.com",
        "password": "admin123456",
        "role": "admin"
    },
    {
        "username": "manager_main",
        "email": "manager@menuapi.com",
        "password": "manager123",
        "role": "manager"
    },
    {
        "username": "customer_test",
        "email": "customer@test.com",
        "password": "customer123",
        "role": "user"
    }
]
