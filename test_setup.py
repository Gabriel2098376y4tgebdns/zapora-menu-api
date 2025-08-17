#!/usr/bin/env python3
"""
Script para testar todas as configurações de qualidade.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Executa um comando e retorna True se bem-sucedido."""
    print(f"\n🔄 {description}")
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {description} - SUCESSO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALHOU")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    """Função principal para testar configurações."""
    print("🚀 Testando Configurações de Qualidade e Automação")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("my_menu_api").exists():
        print("❌ Erro: Execute este script no diretório raiz do projeto")
        sys.exit(1)
    
    tests = [
        ("python -m pytest --version", "Verificar pytest"),
        ("black --version", "Verificar Black"),
        ("flake8 --version", "Verificar Flake8"),
        ("mypy --version", "Verificar mypy"),
        ("coverage --version", "Verificar Coverage"),
        ("bandit --version", "Verificar Bandit"),
        ("safety --version", "Verificar Safety"),
    ]
    
    print("\n📋 Verificando Ferramentas Instaladas:")
    tools_ok = True
    for command, description in tests:
        if not run_command(command, description):
            tools_ok = False
    
    if not tools_ok:
        print("\n❌ Algumas ferramentas não estão instaladas.")
        print("Execute: pip install -e \".[dev]\"")
        sys.exit(1)
    
    print("\n🧪 Executando Verificações de Qualidade:")
    
    quality_checks = [
        ("black --check --diff my_menu_api tests", "Verificar formatação Black"),
        ("flake8 my_menu_api tests", "Executar Flake8 linting"),
        ("mypy my_menu_api", "Executar verificação de tipos mypy"),
        ("bandit -r my_menu_api", "Executar verificação de segurança Bandit"),
        ("safety check", "Verificar vulnerabilidades nas dependências"),
    ]
    
    quality_ok = True
    for command, description in quality_checks:
        if not run_command(command, description):
            quality_ok = False
    
    print("\n🧪 Executando Testes:")
    
    test_commands = [
        ("python -m pytest tests/test_basic.py -v", "Executar teste básico"),
        ("python -m pytest tests/unit/ -v --tb=short", "Executar testes unitários"),
        ("python -m pytest tests/integration/ -v --tb=short", "Executar testes de integração"),
    ]
    
    tests_ok = True
    for command, description in test_commands:
        if not run_command(command, description):
            tests_ok = False
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL:")
    
    if tools_ok:
        print("✅ Todas as ferramentas estão instaladas")
    else:
        print("❌ Algumas ferramentas estão faltando")
    
    if quality_ok:
        print("✅ Todas as verificações de qualidade passaram")
    else:
        print("❌ Algumas verificações de qualidade falharam")
    
    if tests_ok:
        print("✅ Todos os testes passaram")
    else:
        print("❌ Alguns testes falharam")
    
    if tools_ok and quality_ok and tests_ok:
        print("\n🎉 PARABÉNS! Todas as configurações estão funcionando perfeitamente!")
        print("🚀 Seu projeto está pronto para desenvolvimento com qualidade!")
    else:
        print("\n⚠️ Alguns problemas precisam ser resolvidos antes de continuar.")
    
    print("\n📚 Comandos úteis:")
    print("  make help          - Ver todos os comandos disponíveis")
    print("  make dev           - Iniciar servidor de desenvolvimento")
    print("  make test          - Executar todos os testes")
    print("  make quality       - Executar verificações de qualidade")
    print("  make ci-local      - Simular pipeline CI localmente")

if __name__ == "__main__":
    main()
