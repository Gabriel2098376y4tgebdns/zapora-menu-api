#!/usr/bin/env python3
import base64
import secrets

# Gerar secrets seguros
jwt_secret = "K8s-JWT-SecureKey-2024-Production-v1.0-Enterprise-Grade-Security"
admin_password = "SecureAdminPass2024!"
postgres_password = "PostgresSecure2024Enterprise!"

# Converter para base64
jwt_b64 = base64.b64encode(jwt_secret.encode()).decode()
admin_b64 = base64.b64encode(admin_password.encode()).decode()
postgres_b64 = base64.b64encode(postgres_password.encode()).decode()
postgres_user_b64 = base64.b64encode("postgres".encode()).decode()
postgres_db_b64 = base64.b64encode("menuapi".encode()).decode()

# Database URL
db_url = f"postgresql://postgres:{postgres_password}@postgres-service:5432/menuapi"
db_url_b64 = base64.b64encode(db_url.encode()).decode()

# Admin email
admin_email_b64 = base64.b64encode("admin@meuprojeto.dev".encode()).decode()

# Redis URL
redis_url_b64 = base64.b64encode("redis://redis-service:6379/0".encode()).decode()

print("# Valores Base64 para secrets.yaml")
print(f"SECRET_KEY: {jwt_b64}")
print(f"ADMIN_PASSWORD: {admin_b64}")
print(f"ADMIN_EMAIL: {admin_email_b64}")
print(f"POSTGRES_PASSWORD: {postgres_b64}")
print(f"POSTGRES_USER: {postgres_user_b64}")
print(f"POSTGRES_DB: {postgres_db_b64}")
print(f"DATABASE_URL: {db_url_b64}")
print(f"REDIS_URL: {redis_url_b64}")
