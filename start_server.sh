#!/bin/bash
echo "🚀 Iniciando FastAPI Menu API com JWT Authentication..."
echo "📍 Navegando para o diretório do projeto..."
cd /Users/gabrielgimenez/Documents/FastAPI

echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

echo "🌐 Iniciando servidor na porta 8000..."
echo "📚 Documentação disponível em: http://localhost:8000/docs"
echo "🏥 Health check em: http://localhost:8000/health"
echo ""
echo "🔐 Credenciais do admin padrão:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚡ Iniciando servidor..."

uvicorn my_menu_api.main:app --reload --port 8000
