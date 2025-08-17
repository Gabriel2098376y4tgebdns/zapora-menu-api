#!/bin/bash

# FastAPI Menu API - Kubernetes Deployment Script
# Usage: ./deploy.sh [environment] [action]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/k8s"
REGISTRY="your-registry.com"  # Change this to your container registry
IMAGE_NAME="fastapi-menu-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Help function
show_help() {
    cat << EOF
FastAPI Menu API - Kubernetes Deployment Script

Usage: $0 [ENVIRONMENT] [ACTION]

ENVIRONMENTS:
    dev         Deploy to development environment
    staging     Deploy to staging environment
    prod        Deploy to production environment

ACTIONS:
    deploy      Deploy the application (default)
    delete      Delete the application
    status      Show deployment status
    logs        Show application logs
    backup      Create manual database backup
    restore     Restore database from backup
    build       Build and push Docker image
    setup       Setup prerequisites (cert-manager, ingress-nginx)

EXAMPLES:
    $0 dev deploy                 # Deploy to development
    $0 prod status                # Check production status
    $0 staging logs               # View staging logs
    $0 dev backup                 # Create manual backup in dev
    $0 prod restore               # Restore production database

PREREQUISITES:
    - kubectl configured and connected to cluster
    - Docker installed and configured
    - Access to container registry
    - cert-manager installed (for SSL)
    - nginx-ingress installed

EOF
}

# Validate environment
validate_environment() {
    local env=$1
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $env"
        log_info "Valid environments: dev, staging, prod"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed (needed for build action)"
    fi
    
    log_success "Prerequisites check passed"
}

# Setup prerequisites
setup_prerequisites() {
    log_info "Setting up prerequisites..."
    
    # Install cert-manager
    log_info "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    log_info "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
    kubectl wait --for=condition=ready pod -l app=cainjector -n cert-manager --timeout=300s
    kubectl wait --for=condition=ready pod -l app=webhook -n cert-manager --timeout=300s
    
    # Install nginx-ingress
    log_info "Installing nginx-ingress controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
    
    # Wait for nginx-ingress to be ready
    log_info "Waiting for nginx-ingress to be ready..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
    
    log_success "Prerequisites setup completed"
}

# Build and push Docker image
build_and_push() {
    local environment=$1
    local tag="${environment}"
    
    log_info "Building Docker image for environment: $environment"
    
    # Build image
    docker build -t "${IMAGE_NAME}:${tag}" .
    
    # Tag for registry
    docker tag "${IMAGE_NAME}:${tag}" "${REGISTRY}/${IMAGE_NAME}:${tag}"
    
    # Push to registry
    log_info "Pushing image to registry..."
    docker push "${REGISTRY}/${IMAGE_NAME}:${tag}"
    
    log_success "Image built and pushed: ${REGISTRY}/${IMAGE_NAME}:${tag}"
}

# Deploy application
deploy() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_info "Deploying to environment: $environment"
    log_info "Namespace: $namespace"
    
    # Apply base resources
    log_info "Creating namespace..."
    kubectl apply -f "${K8S_DIR}/base/namespace.yaml"
    
    # Apply with kustomize
    log_info "Applying Kubernetes manifests..."
    kubectl apply -k "${K8S_DIR}/environments/${environment}"
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/fastapi-menu-api -n "$namespace" --timeout=600s
    
    # Wait for StatefulSet to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl rollout status statefulset/postgres -n "$namespace" --timeout=600s
    
    log_success "Deployment completed successfully!"
    
    # Show status
    show_status "$environment"
}

# Delete application
delete_deployment() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_warning "Deleting deployment for environment: $environment"
    read -p "Are you sure? This will delete all resources in namespace $namespace [y/N]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete -k "${K8S_DIR}/environments/${environment}"
        log_success "Deployment deleted"
    else
        log_info "Deletion cancelled"
    fi
}

# Show deployment status
show_status() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_info "Status for environment: $environment"
    log_info "Namespace: $namespace"
    
    echo
    echo "=== PODS ==="
    kubectl get pods -n "$namespace" -o wide
    
    echo
    echo "=== SERVICES ==="
    kubectl get services -n "$namespace"
    
    echo
    echo "=== INGRESS ==="
    kubectl get ingress -n "$namespace"
    
    echo
    echo "=== PERSISTENT VOLUMES ==="
    kubectl get pvc -n "$namespace"
    
    echo
    echo "=== RECENT EVENTS ==="
    kubectl get events -n "$namespace" --sort-by='.lastTimestamp' | tail -10
}

# Show application logs
show_logs() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_info "Showing logs for environment: $environment"
    
    # Get pod name
    POD_NAME=$(kubectl get pods -n "$namespace" -l app=fastapi-menu-api -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$POD_NAME" ]; then
        log_error "No pods found for fastapi-menu-api in namespace $namespace"
        exit 1
    fi
    
    log_info "Following logs for pod: $POD_NAME"
    kubectl logs -f "$POD_NAME" -n "$namespace"
}

# Create manual backup
create_backup() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_info "Creating manual backup for environment: $environment"
    
    # Create backup job
    kubectl create job --from=cronjob/postgres-backup "postgres-backup-manual-$(date +%Y%m%d-%H%M%S)" -n "$namespace"
    
    # Wait for job to complete
    log_info "Waiting for backup to complete..."
    kubectl wait --for=condition=complete job -l app=postgres-backup,type=manual -n "$namespace" --timeout=600s
    
    log_success "Manual backup completed"
}

# Restore database
restore_database() {
    local environment=$1
    local namespace="fastapi-menu-api-${environment}"
    
    log_warning "Database restore for environment: $environment"
    
    # List available backups
    log_info "Available backups:"
    kubectl exec -n "$namespace" deployment/postgres-backup -- /scripts/list_backups.sh
    
    read -p "Enter backup filename to restore: " backup_file
    
    if [ -z "$backup_file" ]; then
        log_error "No backup file specified"
        exit 1
    fi
    
    log_warning "This will restore the database from backup: $backup_file"
    read -p "Are you sure? This will overwrite the current database [y/N]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create restore job
        kubectl run postgres-restore-$(date +%Y%m%d-%H%M%S) \
            --image=postgres:15-alpine \
            --rm -i --restart=Never \
            --namespace="$namespace" \
            --overrides='{"spec":{"containers":[{"name":"postgres-restore","image":"postgres:15-alpine","command":["/scripts/restore.sh","'$backup_file'"],"env":[{"name":"POSTGRES_USER","valueFrom":{"secretKeyRef":{"name":"postgres-secret","key":"POSTGRES_USER"}}},{"name":"POSTGRES_PASSWORD","valueFrom":{"secretKeyRef":{"name":"postgres-secret","key":"POSTGRES_PASSWORD"}}},{"name":"POSTGRES_DB","valueFrom":{"secretKeyRef":{"name":"postgres-secret","key":"POSTGRES_DB"}}},{"name":"PGPASSWORD","valueFrom":{"secretKeyRef":{"name":"postgres-secret","key":"POSTGRES_PASSWORD"}}}],"volumeMounts":[{"name":"backup-storage","mountPath":"/backup"},{"name":"backup-scripts","mountPath":"/scripts"}]}],"volumes":[{"name":"backup-storage","persistentVolumeClaim":{"claimName":"backup-pvc"}},{"name":"backup-scripts","configMap":{"name":"backup-scripts","defaultMode":493}}]}}'
        
        log_success "Database restore completed"
    else
        log_info "Restore cancelled"
    fi
}

# Main script
main() {
    local environment=${1:-""}
    local action=${2:-"deploy"}
    
    # Show help if no arguments
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Handle special actions that don't require environment
    case $action in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        "setup")
            check_prerequisites
            setup_prerequisites
            exit 0
            ;;
    esac
    
    # Validate environment
    validate_environment "$environment"
    
    # Check prerequisites
    check_prerequisites
    
    # Execute action
    case $action in
        "deploy")
            deploy "$environment"
            ;;
        "delete")
            delete_deployment "$environment"
            ;;
        "status")
            show_status "$environment"
            ;;
        "logs")
            show_logs "$environment"
            ;;
        "backup")
            create_backup "$environment"
            ;;
        "restore")
            restore_database "$environment"
            ;;
        "build")
            build_and_push "$environment"
            ;;
        *)
            log_error "Unknown action: $action"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
