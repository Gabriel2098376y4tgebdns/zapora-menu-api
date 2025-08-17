#!/bin/bash

# FastAPI Menu API Management Script
# Provides convenient commands for development and production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="FastAPI Menu API"
VENV_PATH="venv"
REQUIREMENTS_FILE="my_menu_api/requirements.txt"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) == 0 ]]; then
        log_error "Python 3.8+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python $PYTHON_VERSION detected"
}

create_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv $VENV_PATH
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
}

activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source $VENV_PATH/bin/activate
        log_success "Virtual environment activated"
    else
        log_error "Virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r $REQUIREMENTS_FILE
    log_success "Dependencies installed"
}

setup_project() {
    log_info "Setting up $PROJECT_NAME..."
    check_python
    create_venv
    activate_venv
    install_dependencies
    
    # Create necessary directories
    mkdir -p uploads/{originals,large,medium,small,thumbnails}
    mkdir -p logs
    mkdir -p monitoring/grafana/{provisioning,dashboards}
    
    log_success "Project setup completed!"
    log_info "Run './manage.sh dev' to start development server"
}

run_development() {
    log_info "Starting development server..."
    activate_venv
    
    export ENVIRONMENT=development
    export DEBUG=true
    export DATABASE_URL=${DATABASE_URL:-"sqlite:///./sql_app.db"}
    
    uvicorn my_menu_api.main:app --host 0.0.0.0 --port 8000 --reload
}

run_production() {
    log_info "Starting production server..."
    activate_venv
    
    export ENVIRONMENT=production
    export DEBUG=false
    
    # Check required environment variables
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is required for production"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        log_error "SECRET_KEY environment variable is required for production"
        exit 1
    fi
    
    uvicorn my_menu_api.main:app --host 0.0.0.0 --port 8000 --workers 4
}

run_tests() {
    log_info "Running tests..."
    activate_venv
    
    export ENVIRONMENT=testing
    export DATABASE_URL="sqlite:///./test.db"
    
    pytest tests/ -v --cov=my_menu_api --cov-report=html --cov-report=term
    log_success "Tests completed. Coverage report available in htmlcov/"
}

run_docker() {
    log_info "Starting Docker environment..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    docker-compose up --build -d
    log_success "Docker environment started"
    log_info "API: http://localhost:8000"
    log_info "Prometheus: http://localhost:9090"
    log_info "Grafana: http://localhost:3000 (admin/admin123)"
}

stop_docker() {
    log_info "Stopping Docker environment..."
    docker-compose down
    log_success "Docker environment stopped"
}

create_migration() {
    if [ -z "$2" ]; then
        log_error "Migration message is required"
        log_info "Usage: ./manage.sh migrate \"migration message\""
        exit 1
    fi
    
    log_info "Creating migration: $2"
    activate_venv
    
    python -m my_menu_api.migration_utils migrate -m "$2"
    log_success "Migration created"
}

run_migrations() {
    log_info "Running database migrations..."
    activate_venv
    
    python -m my_menu_api.migration_utils upgrade
    log_success "Migrations completed"
}

lint_code() {
    log_info "Linting code..."
    activate_venv
    
    # Install linting tools if not present
    pip install black isort flake8 mypy
    
    log_info "Running Black (code formatting)..."
    black my_menu_api/ tests/
    
    log_info "Running isort (import sorting)..."
    isort my_menu_api/ tests/
    
    log_info "Running flake8 (style guide)..."
    flake8 my_menu_api/ tests/ --max-line-length=88 --extend-ignore=E203,W503
    
    log_info "Running mypy (type checking)..."
    mypy my_menu_api/ --ignore-missing-imports
    
    log_success "Code linting completed"
}

check_health() {
    log_info "Checking application health..."
    
    # Check if the application is running
    if curl -f http://localhost:8000/healthz &> /dev/null; then
        log_success "Application is healthy"
        
        # Show detailed health information
        echo ""
        log_info "Detailed health check:"
        curl -s http://localhost:8000/health/detailed | python -m json.tool
    else
        log_error "Application is not responding"
        exit 1
    fi
}

show_logs() {
    log_info "Showing application logs..."
    
    if [ -f "logs/app.log" ]; then
        tail -f logs/app.log
    else
        log_warning "No log file found. Application may not be running."
    fi
}

backup_database() {
    log_info "Creating database backup..."
    
    BACKUP_DIR="backups"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p $BACKUP_DIR
    
    if [ "$ENVIRONMENT" = "production" ]; then
        # Production backup (PostgreSQL)
        pg_dump $DATABASE_URL > $BACKUP_FILE
    else
        # Development backup (SQLite)
        cp sql_app.db "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).db"
    fi
    
    log_success "Database backup created: $BACKUP_FILE"
}

show_usage() {
    echo -e "${BLUE}$PROJECT_NAME Management Script${NC}"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Available commands:"
    echo "  setup           - Set up the project (create venv, install dependencies)"
    echo "  dev             - Start development server"
    echo "  prod            - Start production server"
    echo "  test            - Run tests with coverage"
    echo "  docker          - Start Docker environment"
    echo "  docker-stop     - Stop Docker environment"
    echo "  migrate <msg>   - Create new database migration"
    echo "  upgrade         - Run database migrations"
    echo "  lint            - Run code linting and formatting"
    echo "  health          - Check application health"
    echo "  logs            - Show application logs"
    echo "  backup          - Create database backup"
    echo "  help            - Show this help message"
    echo ""
    echo "Environment variables for production:"
    echo "  DATABASE_URL    - PostgreSQL database URL"
    echo "  SECRET_KEY      - JWT secret key"
    echo "  REDIS_URL       - Redis connection URL"
    echo ""
}

# Main command processing
case "$1" in
    setup)
        setup_project
        ;;
    dev)
        run_development
        ;;
    prod)
        run_production
        ;;
    test)
        run_tests
        ;;
    docker)
        run_docker
        ;;
    docker-stop)
        stop_docker
        ;;
    migrate)
        create_migration "$@"
        ;;
    upgrade)
        run_migrations
        ;;
    lint)
        lint_code
        ;;
    health)
        check_health
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_database
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        log_error "No command specified"
        show_usage
        exit 1
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
