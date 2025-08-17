# Deployment Scripts

## Quick Deploy to Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway init
railway up
```

## Docker Deployment
```bash
# Build image
docker build -t menu-api .

# Run container
docker run -d -p 8000:8000 --env-file .env menu-api
```

## Environment Setup
```bash
# Production environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export SECRET_KEY="your-production-secret-key"
export ENVIRONMENT="production"
export DEBUG="false"
```

## Health Check
```bash
# Test API health
curl -X GET "https://your-domain.com/health"
```

## Migration Commands
```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
