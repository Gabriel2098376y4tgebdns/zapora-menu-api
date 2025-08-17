# FastAPI Menu API - Development Makefile
.PHONY: help install install-dev clean test test-unit test-integration coverage lint format type-check security run dev docs build

# Default target
help:
	@echo "🚀 FastAPI Menu API - Development Commands"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install     Install production dependencies"
	@echo "  install-dev Install development dependencies"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  coverage    Generate coverage report"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint        Run linting (flake8)"
	@echo "  format      Format code (black)"
	@echo "  type-check  Run type checking (mypy)"
	@echo "  security    Run security checks"
	@echo "  quality     Run all quality checks"
	@echo ""
	@echo "🏃 Development:"
	@echo "  run         Run production server"
	@echo "  dev         Run development server with auto-reload"
	@echo "  docs        Open API documentation"
	@echo ""
	@echo "🏗️ Build:"
	@echo "  build       Build package"
	@echo "  clean       Clean build artifacts"

# =================== INSTALLATION ===================
install:
	@echo "📦 Installing production dependencies..."
	pip install -e .

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -e ".[dev]"
	pre-commit install

# =================== TESTING ===================
test:
	@echo "🧪 Running all tests..."
	pytest -v --cov=my_menu_api --cov-report=term-missing --cov-report=html

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v --cov=my_menu_api --cov-report=term-missing

test-integration:
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ -v --cov=my_menu_api --cov-report=term-missing

coverage:
	@echo "📊 Generating coverage report..."
	pytest --cov=my_menu_api --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report generated in htmlcov/"
	@echo "🌐 Open htmlcov/index.html in your browser"

# =================== CODE QUALITY ===================
lint:
	@echo "🔍 Running flake8 linting..."
	flake8 my_menu_api tests

format:
	@echo "🎨 Formatting code with black..."
	black my_menu_api tests
	@echo "📚 Sorting imports with isort..."
	isort my_menu_api tests

type-check:
	@echo "🔒 Running mypy type checking..."
	mypy my_menu_api

security:
	@echo "🛡️ Running security checks..."
	@echo "🔐 Checking dependencies with safety..."
	safety check || true
	@echo "🔍 Running bandit security scan..."
	bandit -r my_menu_api || true

quality: format lint type-check security
	@echo "✅ All quality checks completed!"

# =================== DEVELOPMENT ===================
run:
	@echo "🚀 Starting production server..."
	uvicorn my_menu_api.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "🏃 Starting development server with auto-reload..."
	uvicorn my_menu_api.main:app --reload --host 0.0.0.0 --port 8000

docs:
	@echo "📚 Opening API documentation..."
	@echo "🌐 Swagger UI: http://localhost:8000/docs"
	@echo "🌐 ReDoc: http://localhost:8000/redoc"

# =================== BUILD ===================
build:
	@echo "📦 Building package..."
	python -m build

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# =================== DOCKER (BONUS) ===================
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t fastapi-menu-api .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 fastapi-menu-api

# =================== DATABASE ===================
db-upgrade:
	@echo "🗄️ Running database migrations..."
	# Add your migration commands here

db-downgrade:
	@echo "🗄️ Reverting database migrations..."
	# Add your migration rollback commands here

# =================== CI/CD SIMULATION ===================
ci-local:
	@echo "🔄 Running CI pipeline locally..."
	make format
	make lint
	make type-check
	make security
	make test
	@echo "✅ Local CI pipeline completed!"
