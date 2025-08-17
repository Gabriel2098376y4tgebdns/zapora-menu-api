"""
Teste básico para verificar configuração.
"""

import pytest
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_imports():
    """Testa se as importações básicas funcionam."""
    try:
        from my_menu_api import models
        from my_menu_api import schemas
        from my_menu_api.database import Base
        assert True
    except ImportError as e:
        pytest.fail(f"Falha na importação: {e}")

def test_basic_math():
    """Teste básico para verificar se pytest está funcionando."""
    assert 2 + 2 == 4
    assert "hello" == "hello"
    assert [1, 2, 3] == [1, 2, 3]
