#!/usr/bin/env python3
"""
Script para testar se as dependências estão instaladas corretamente.
"""

def test_imports():
    """Testa se todas as dependências necessárias estão instaladas."""
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy: {e}")
    
    try:
        import pydantic
        print(f"✅ Pydantic: {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Pydantic: {e}")
    
    try:
        from jose import jwt
        print("✅ python-jose: Instalado")
    except ImportError as e:
        print(f"❌ python-jose: {e}")
    
    try:
        from passlib.context import CryptContext
        print("✅ passlib: Instalado")
    except ImportError as e:
        print(f"❌ passlib: {e}")
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")

if __name__ == "__main__":
    print("🔍 Testando dependências do projeto...\n")
    test_imports()
    print("\n✅ Teste de dependências concluído!")
