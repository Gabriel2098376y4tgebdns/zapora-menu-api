#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema de autenticação está funcionando.
"""

import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_authentication_system():
    """Testa o sistema de autenticação."""
    try:
        print("🔐 Testando sistema de autenticação...")
        
        # Test 1: Importações básicas
        print("1. Testando importações...")
        from my_menu_api.auth import get_password_hash, verify_password, create_access_token
        from my_menu_api.models import User, UserRole
        from my_menu_api.schemas import UserCreate
        print("   ✅ Importações OK")
        
        # Test 2: Hash de senha
        print("2. Testando hash de senha...")
        password = "MinhaSenh@123"
        hashed = get_password_hash(password)
        is_valid = verify_password(password, hashed)
        print(f"   ✅ Hash funciona: {is_valid}")
        
        # Test 3: Criação de token
        print("3. Testando criação de token...")
        token_data = {
            "sub": "admin",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin"
        }
        token = create_access_token(token_data)
        print(f"   ✅ Token criado: {len(token)} caracteres")
        
        print("\n✅ Sistema de autenticação funcionando!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no sistema de autenticação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Testa os modelos do banco de dados."""
    try:
        print("\n🗄️ Testando modelos do banco...")
        
        from my_menu_api.models import Base, User, MenuItem, UserRole
        from my_menu_api.database import engine
        
        # Criar tabelas
        print("1. Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Tabelas criadas")
        
        print("\n✅ Modelos do banco funcionando!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nos modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do sistema...\n")
    
    auth_ok = test_authentication_system()
    db_ok = test_database_models()
    
    if auth_ok and db_ok:
        print("\n🎉 Todos os testes passaram! Sistema pronto para uso.")
        print("\n📋 Próximos passos:")
        print("   1. Execute: uvicorn my_menu_api.main:app --reload")
        print("   2. Acesse: http://localhost:8000/docs")
        print("   3. Teste o login com:")
        print("      - Username: admin")
        print("      - Password: admin123")
    else:
        print("\n⚠️ Há problemas no sistema que precisam ser corrigidos.")
