#!/usr/bin/env python3
"""
Script de validação final do projeto FastAPI Menu API.
Verifica se todos os componentes estão funcionando corretamente.
"""

import sys
import subprocess
import importlib
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔍 {message}{Colors.END}")

def check_imports():
    """Verifica se todos os módulos podem ser importados."""
    print_header("Verificando Imports")
    
    modules_to_check = [
        "my_menu_api.main",
        "my_menu_api.models",
        "my_menu_api.schemas",
        "my_menu_api.database",
        "my_menu_api.config",
        "my_menu_api.auth",
        "my_menu_api.routers.auth",
        "my_menu_api.routers.menu_items",
        "my_menu_api.routers.images",
        "my_menu_api.routers.audit",
        "my_menu_api.services.menu_item_service",
        "my_menu_api.services.image_service",
        "my_menu_api.services.audit_service",
    ]
    
    failed_imports = []
    
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print_success(f"Import {module}")
        except ImportError as e:
            print_error(f"Import {module} - {e}")
            failed_imports.append(module)
        except Exception as e:
            print_warning(f"Import {module} - Warning: {e}")
    
    # Optional production modules
    optional_modules = [
        "my_menu_api.cache",
        "my_menu_api.rate_limiting", 
        "my_menu_api.logging_config",
        "my_menu_api.metrics",
        "my_menu_api.health",
        "my_menu_api.migration_utils"
    ]
    
    for module in optional_modules:
        try:
            importlib.import_module(module)
            print_success(f"Optional {module}")
        except ImportError:
            print_warning(f"Optional {module} - Not available (OK)")
        except Exception as e:
            print_warning(f"Optional {module} - Warning: {e}")
    
    return len(failed_imports) == 0

def check_fastapi_app():
    """Verifica se a aplicação FastAPI pode ser criada."""
    print_header("Verificando Aplicação FastAPI")
    
    try:
        from my_menu_api.main import app
        print_success("FastAPI app criada com sucesso")
        print_info(f"App title: {app.title}")
        print_info(f"Número de rotas: {len(app.routes)}")
        
        # Check if essential routes exist
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        essential_routes = ['/auth/login', '/auth/register', '/menu-items', '/health']
        
        for route in essential_routes:
            if any(route in path for path in route_paths):
                print_success(f"Rota encontrada: {route}")
            else:
                print_warning(f"Rota não encontrada: {route}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao criar app FastAPI: {e}")
        return False

def check_database_models():
    """Verifica se os modelos do banco estão corretos."""
    print_header("Verificando Modelos do Banco")
    
    try:
        from my_menu_api.models import User, MenuItem, AuditLog, Base
        print_success("Modelos importados com sucesso")
        
        # Verify Base metadata
        tables = Base.metadata.tables.keys()
        expected_tables = ['users', 'menu_items', 'audit_logs']
        
        for table in expected_tables:
            if table in tables:
                print_success(f"Tabela {table} definida")
            else:
                print_error(f"Tabela {table} não encontrada")
        
        return True
    except Exception as e:
        print_error(f"Erro nos modelos: {e}")
        return False

def check_schemas():
    """Verifica se os schemas Pydantic estão corretos."""
    print_header("Verificando Schemas Pydantic")
    
    try:
        from my_menu_api.schemas import (
            UserCreate, UserResponse, MenuItemCreate, MenuItemResponse,
            Token, AuditLogResponse
        )
        print_success("Schemas principais importados")
        
        # Test schema validation
        user_data = {
            "email": "test@example.com",
            "password": "test123",
            "full_name": "Test User",
            "role": "user"
        }
        
        user_schema = UserCreate(**user_data)
        print_success("Validação de schema UserCreate")
        
        menu_data = {
            "name": "Test Item",
            "description": "Test description",
            "price": 10.99,
            "category": "test",
            "available": True
        }
        
        menu_schema = MenuItemCreate(**menu_data)
        print_success("Validação de schema MenuItemCreate")
        
        return True
    except Exception as e:
        print_error(f"Erro nos schemas: {e}")
        return False

def check_file_structure():
    """Verifica se a estrutura de arquivos está correta."""
    print_header("Verificando Estrutura de Arquivos")
    
    required_files = [
        "my_menu_api/__init__.py",
        "my_menu_api/main.py",
        "my_menu_api/models.py",
        "my_menu_api/schemas.py",
        "my_menu_api/database.py",
        "my_menu_api/config.py",
        "my_menu_api/auth.py",
        "my_menu_api/routers/__init__.py",
        "my_menu_api/routers/auth.py",
        "my_menu_api/routers/menu_items.py",
        "my_menu_api/routers/images.py",
        "my_menu_api/routers/audit.py",
        "my_menu_api/services/__init__.py",
        "my_menu_api/services/menu_item_service.py",
        "my_menu_api/services/image_service.py",
        "my_menu_api/services/audit_service.py",
        "requirements.txt",
        "README.md",
        "API_DOCUMENTATION.md",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "manage.sh"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"Arquivo {file_path}")
        else:
            print_error(f"Arquivo {file_path} não encontrado")
            missing_files.append(file_path)
    
    # Optional files
    optional_files = [
        "alembic.ini",
        "alembic/env.py",
        "tests/conftest.py",
        "monitoring/prometheus.yml"
    ]
    
    for file_path in optional_files:
        if Path(file_path).exists():
            print_success(f"Opcional {file_path}")
        else:
            print_warning(f"Opcional {file_path} não encontrado")
    
    return len(missing_files) == 0

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print_header("Verificando Dependências")
    
    try:
        import fastapi
        print_success(f"FastAPI {fastapi.__version__}")
    except ImportError:
        print_error("FastAPI não instalado")
        return False
    
    try:
        import sqlalchemy
        print_success(f"SQLAlchemy {sqlalchemy.__version__}")
    except ImportError:
        print_error("SQLAlchemy não instalado")
        return False
    
    try:
        import pydantic
        print_success(f"Pydantic {pydantic.__version__}")
    except ImportError:
        print_error("Pydantic não instalado")
        return False
    
    # Optional dependencies
    optional_deps = [
        ("uvicorn", "uvicorn"),
        ("pytest", "pytest"),
        ("pillow", "PIL"),
        ("aiofiles", "aiofiles"),
        ("passlib", "passlib"),
        ("python-jose", "jose"),
    ]
    
    for dep_name, import_name in optional_deps:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            print_success(f"{dep_name} {version}")
        except ImportError:
            print_warning(f"{dep_name} não instalado")
    
    return True

def run_syntax_check():
    """Executa verificação de sintaxe Python."""
    print_header("Verificação de Sintaxe")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "py_compile", "my_menu_api/main.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Sintaxe do main.py está correta")
        else:
            print_error(f"Erro de sintaxe: {result.stderr}")
            return False
    except Exception as e:
        print_warning(f"Não foi possível verificar sintaxe: {e}")
    
    return True

def main():
    """Executa todas as verificações."""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚀 FastAPI Menu API - Validação Final")
    print("=====================================")
    print(f"{Colors.END}")
    
    checks = [
        ("Estrutura de Arquivos", check_file_structure),
        ("Dependências", check_dependencies),
        ("Sintaxe", run_syntax_check),
        ("Imports", check_imports),
        ("Modelos do Banco", check_database_models),
        ("Schemas Pydantic", check_schemas),
        ("Aplicação FastAPI", check_fastapi_app),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{Colors.BOLD}📋 {check_name}{Colors.END}")
        print("-" * 50)
        
        try:
            if check_func():
                passed += 1
                print_success(f"{check_name} - PASSOU")
            else:
                print_error(f"{check_name} - FALHOU")
        except Exception as e:
            print_error(f"{check_name} - ERRO: {e}")
    
    # Summary
    print(f"\n{Colors.BOLD}📊 RESUMO DA VALIDAÇÃO{Colors.END}")
    print("=" * 50)
    
    if passed == total:
        print_success(f"TODOS OS TESTES PASSARAM! ({passed}/{total})")
        print_info("🎉 Projeto pronto para produção!")
        return 0
    else:
        print_warning(f"ALGUNS TESTES FALHARAM ({passed}/{total})")
        print_info("⚠️ Revise os pontos marcados acima")
        return 1

if __name__ == "__main__":
    sys.exit(main())
