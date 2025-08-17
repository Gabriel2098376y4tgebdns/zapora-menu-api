# 📖 FastAPI Menu API - Documentação Completa

## 🎯 Visão Geral

A **FastAPI Menu API** é uma API RESTful completa para gerenciamento de cardápios, desenvolvida com **FastAPI**, **SQLAlchemy**, e infraestrutura de produção robusta. Oferece autenticação JWT, upload de imagens, auditoria, cache e muito mais.

> **🔒 100% Segura - Auditoria de Segurança Aprovada ✅**
> 
> - ✅ Zero secrets hardcoded  
> - ✅ Validação automática de segurança
> - ✅ Credenciais de produção fortes
> - ✅ SSL/TLS obrigatório
> - ✅ Headers de segurança enterprise

### 🏗️ Arquitetura da API

```
FastAPI Menu API
├── 🔐 Autenticação JWT (roles: User, Manager, Admin)
├── 🍽️ Gerenciamento de Menu Items
├── 🖼️ Upload e Processamento de Imagens
├── 📋 Sistema de Auditoria
├── 🏥 Health Checks
├── 📊 Métricas Prometheus
└── ⚡ Cache Redis (opcional)
```

---

## 🔗 Base URL

- **Desenvolvimento**: `http://localhost:8000`
- **Produção**: `https://your-domain.com`

---

## 🔐 Autenticação

A API utiliza **JWT (JSON Web Tokens)** para autenticação. Todos os endpoints protegidos requerem o header:

```http
Authorization: Bearer <jwt_token>
```

### 📝 Registro de Usuário

**`POST /auth/register`**

Registra um novo usuário no sistema.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "senha123",
  "full_name": "João Silva",
  "role": "user"
}
```

#### Response (201 Created)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "João Silva",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Possible Status Codes
- `201 Created` - Usuário criado com sucesso
- `400 Bad Request` - Dados inválidos ou email já existe
- `422 Unprocessable Entity` - Erro de validação

---

### 🔑 Login

**`POST /auth/login`**

Autentica um usuário e retorna um token JWT.

#### Request Body (Form Data)
```http
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=senha123
```

#### Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "João Silva",
    "role": "user"
  }
}
```

#### Possible Status Codes
- `200 OK` - Login realizado com sucesso
- `401 Unauthorized` - Credenciais inválidas
- `422 Unprocessable Entity` - Dados mal formatados

---

### 👤 Perfil do Usuário

**`GET /auth/me`**

Retorna informações do usuário autenticado.

#### Headers
```http
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "João Silva",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Possible Status Codes
- `200 OK` - Perfil retornado com sucesso
- `401 Unauthorized` - Token inválido ou expirado

---

## 🍽️ Menu Items

### 📋 Listar Itens do Menu

**`GET /menu-items`**

Lista todos os itens do menu com paginação e filtros opcionais.

#### Query Parameters
| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|---------|
| `category` | string | Filtrar por categoria | - |
| `available` | boolean | Filtrar por disponibilidade | - |
| `skip` | integer | Número de itens para pular | 0 |
| `limit` | integer | Número máximo de itens | 100 |

#### Example Request
```http
GET /menu-items?category=bebidas&available=true&skip=0&limit=10
```

#### Response (200 OK)
```json
{
  "items": [
    {
      "id": 1,
      "name": "Hambúrguer Clássico",
      "description": "Hambúrguer com carne, queijo, alface e tomate",
      "price": 25.90,
      "category": "lanches",
      "available": true,
      "image_url": "/static/images/hamburger.jpg",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10,
  "has_next": false
}
```

#### Possible Status Codes
- `200 OK` - Lista retornada com sucesso
- `422 Unprocessable Entity` - Parâmetros inválidos

---

### 🔍 Obter Item Específico

**`GET /menu-items/{item_id}`**

Retorna detalhes de um item específico do menu.

#### Path Parameters
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `item_id` | integer | ID do item |

#### Response (200 OK)
```json
{
  "id": 1,
  "name": "Hambúrguer Clássico",
  "description": "Hambúrguer com carne, queijo, alface e tomate",
  "price": 25.90,
  "category": "lanches",
  "available": true,
  "image_url": "/static/images/hamburger.jpg",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Possible Status Codes
- `200 OK` - Item encontrado
- `404 Not Found` - Item não existe

---

### ➕ Criar Item do Menu

**`POST /menu-items`** 🔒 *Requer: Manager ou Admin*

Cria um novo item no menu.

#### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "name": "Pizza Margherita",
  "description": "Pizza com molho de tomate, mussarela e manjericão",
  "price": 35.90,
  "category": "pizzas",
  "available": true,
  "image_url": "/static/images/pizza-margherita.jpg"
}
```

#### Response (201 Created)
```json
{
  "id": 2,
  "name": "Pizza Margherita",
  "description": "Pizza com molho de tomate, mussarela e manjericão",
  "price": 35.90,
  "category": "pizzas",
  "available": true,
  "image_url": "/static/images/pizza-margherita.jpg",
  "created_at": "2024-01-01T12:30:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

#### Possible Status Codes
- `201 Created` - Item criado com sucesso
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissão insuficiente
- `422 Unprocessable Entity` - Erro de validação

---

### ✏️ Atualizar Item do Menu

**`PUT /menu-items/{item_id}`** 🔒 *Requer: Manager ou Admin*

Atualiza um item existente no menu.

#### Path Parameters
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `item_id` | integer | ID do item |

#### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "name": "Pizza Margherita Premium",
  "description": "Pizza com molho de tomate especial, mussarela premium e manjericão fresco",
  "price": 39.90,
  "category": "pizzas",
  "available": true,
  "image_url": "/static/images/pizza-margherita-premium.jpg"
}
```

#### Response (200 OK)
```json
{
  "id": 2,
  "name": "Pizza Margherita Premium",
  "description": "Pizza com molho de tomate especial, mussarela premium e manjericão fresco",
  "price": 39.90,
  "category": "pizzas",
  "available": true,
  "image_url": "/static/images/pizza-margherita-premium.jpg",
  "created_at": "2024-01-01T12:30:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

#### Possible Status Codes
- `200 OK` - Item atualizado com sucesso
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissão insuficiente
- `404 Not Found` - Item não existe
- `422 Unprocessable Entity` - Erro de validação

---

### 🗑️ Deletar Item do Menu

**`DELETE /menu-items/{item_id}`** 🔒 *Requer: Admin*

Remove um item do menu.

#### Path Parameters
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `item_id` | integer | ID do item |

#### Headers
```http
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)
```json
{
  "message": "Item removido com sucesso",
  "item_id": 2
}
```

#### Possible Status Codes
- `200 OK` - Item removido com sucesso
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissão insuficiente (apenas Admin)
- `404 Not Found` - Item não existe

---

## 🖼️ Upload de Imagens

### 📤 Upload de Imagem

**`POST /images/upload`** 🔒 *Requer: Manager ou Admin*

Faz upload de uma imagem com redimensionamento automático.

#### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

#### Request Body (Form Data)
```http
Content-Type: multipart/form-data

file=@hamburger.jpg
```

#### Response (201 Created)
```json
{
  "filename": "hamburger_20240101_120000.jpg",
  "path": "/static/images/hamburger_20240101_120000.jpg",
  "url": "http://localhost:8000/static/images/hamburger_20240101_120000.jpg",
  "size": 245760,
  "content_type": "image/jpeg",
  "variants": {
    "original": "/static/originals/hamburger_20240101_120000.jpg",
    "large": "/static/large/hamburger_20240101_120000.jpg",
    "medium": "/static/medium/hamburger_20240101_120000.jpg",
    "small": "/static/small/hamburger_20240101_120000.jpg",
    "thumbnail": "/static/thumbnails/hamburger_20240101_120000.jpg"
  }
}
```

#### File Specifications
- **Formatos aceitos**: JPG, JPEG, PNG, GIF, WEBP
- **Tamanho máximo**: 5MB
- **Redimensionamentos automáticos**:
  - Original: Tamanho original (limitado)
  - Large: 1200x800px
  - Medium: 800x600px
  - Small: 400x300px
  - Thumbnail: 150x150px

#### Possible Status Codes
- `201 Created` - Upload realizado com sucesso
- `400 Bad Request` - Arquivo inválido ou muito grande
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissão insuficiente
- `413 Payload Too Large` - Arquivo muito grande
- `415 Unsupported Media Type` - Formato não suportado

---

### 🗑️ Deletar Imagem

**`DELETE /images/{filename}`** 🔒 *Requer: Manager ou Admin*

Remove uma imagem e todas suas variações.

#### Path Parameters
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `filename` | string | Nome do arquivo |

#### Headers
```http
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)
```json
{
  "message": "Imagem hamburger_20240101_120000.jpg removida com sucesso",
  "deleted_files": [
    "original/hamburger_20240101_120000.jpg",
    "large/hamburger_20240101_120000.jpg",
    "medium/hamburger_20240101_120000.jpg",
    "small/hamburger_20240101_120000.jpg",
    "thumbnails/hamburger_20240101_120000.jpg"
  ]
}
```

#### Possible Status Codes
- `200 OK` - Imagem removida com sucesso
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissão insuficiente
- `404 Not Found` - Imagem não encontrada

---

### 📋 Listar Imagens

**`GET /images/`** 🔒 *Requer: Autenticação*

Lista todas as imagens uploadadas.

#### Headers
```http
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)
```json
{
  "total": 2,
  "images": [
    {
      "filename": "hamburger_20240101_120000.jpg",
      "size": 245760,
      "content_type": "image/jpeg",
      "uploaded_at": "2024-01-01T12:00:00Z",
      "url": "/static/images/hamburger_20240101_120000.jpg"
    },
    {
      "filename": "pizza_20240101_130000.jpg",
      "size": 312450,
      "content_type": "image/jpeg",
      "uploaded_at": "2024-01-01T13:00:00Z",
      "url": "/static/images/pizza_20240101_130000.jpg"
    }
  ]
}
```

---

## 📋 Auditoria

### 📜 Logs de Auditoria

**`GET /audit/logs`** 🔒 *Requer: Admin*

Retorna logs de auditoria das operações realizadas.

#### Headers
```http
Authorization: Bearer <jwt_token>
```

#### Query Parameters
| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|---------|
| `action` | string | Filtrar por ação | - |
| `user_id` | integer | Filtrar por usuário | - |
| `start_date` | string | Data inicial (ISO) | - |
| `end_date` | string | Data final (ISO) | - |
| `skip` | integer | Paginação | 0 |
| `limit` | integer | Limite de itens | 100 |

#### Response (200 OK)
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "action": "CREATE_MENU_ITEM",
      "resource_type": "menu_item",
      "resource_id": 2,
      "details": {
        "item_name": "Pizza Margherita",
        "category": "pizzas"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-01T12:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

#### Possible Status Codes
- `200 OK` - Logs retornados com sucesso
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Apenas Admins podem acessar

---

## 🏥 Health Checks

### ⚡ Health Check Básico

**`GET /healthz`**

Verifica se a aplicação está respondendo.

#### Response (200 OK)
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### 🔍 Readiness Check

**`GET /readiness`**

Verifica se todas as dependências estão disponíveis.

#### Response (200 OK)
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T12:00:00Z",
  "check_duration": 0.0234,
  "checks": {
    "database": {
      "status": "healthy",
      "connectivity_time": 0.0123,
      "query_time": 0.0089
    },
    "redis": {
      "status": "healthy",
      "ping_time": 0.0045,
      "operation_time": 0.0067
    },
    "external_services": {
      "status": "healthy",
      "services": []
    }
  }
}
```

#### Possible Status Codes
- `200 OK` - Sistema pronto
- `503 Service Unavailable` - Dependências indisponíveis

---

### 💓 Liveness Check

**`GET /liveness`**

Verifica se a aplicação está funcionando internamente.

#### Response (200 OK)
```json
{
  "status": "alive",
  "timestamp": "2024-01-01T12:00:00Z",
  "check_duration": 0.0012,
  "application": {
    "status": "healthy",
    "uptime_seconds": 3600.45,
    "event_loop": "healthy"
  }
}
```

---

### 📊 Health Check Detalhado

**`GET /health/detailed`**

Status completo de todos os componentes do sistema.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "check_duration": 0.0567,
  "checks": {
    "application": {
      "status": "healthy",
      "uptime_seconds": 3600.45,
      "event_loop": "healthy"
    },
    "database": {
      "status": "healthy",
      "connectivity_time": 0.0123,
      "query_time": 0.0089,
      "pool_info": {
        "size": 5,
        "checked_in": 3,
        "checked_out": 2
      }
    },
    "redis": {
      "status": "healthy",
      "ping_time": 0.0045,
      "operation_time": 0.0067,
      "connected_clients": 12,
      "used_memory": "2.5M",
      "uptime": 86400
    }
  },
  "unhealthy_components": []
}
```

---

## 📊 Métricas

### 📈 Prometheus Metrics

**`GET /metrics`**

Endpoint de métricas no formato Prometheus.

#### Response (200 OK)
```prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/menu-items",status_code="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/menu-items",le="0.1"} 945
http_request_duration_seconds_bucket{method="GET",endpoint="/menu-items",le="0.5"} 1200

# HELP database_connections_active Active database connections
# TYPE database_connections_active gauge
database_connections_active 3

# HELP cache_hits_total Cache hits
# TYPE cache_hits_total counter
cache_hits_total 567

# HELP active_users Current active users
# TYPE active_users gauge
active_users 25
```

#### Content-Type
```
text/plain; version=0.0.4; charset=utf-8
```

---

## 🚫 Rate Limiting

A API implementa rate limiting para prevenir abuso:

### Limites Padrão

| Endpoint | Limite | Janela |
|----------|--------|---------|
| **Global** | 100 requests | 60 segundos |
| **POST /auth/login** | 5 requests | 60 segundos |
| **POST /images/upload** | 10 requests | 300 segundos |

### Headers de Rate Limit

Todas as respostas incluem headers informativos:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1704110400
X-RateLimit-Window: 60
```

### Response de Rate Limit Excedido (429)

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45,
  "limit": 100,
  "window": 60
}
```

---

## 🎯 Códigos de Status HTTP

### Códigos de Sucesso
- `200 OK` - Operação realizada com sucesso
- `201 Created` - Recurso criado com sucesso
- `204 No Content` - Operação realizada sem retorno

### Códigos de Erro do Cliente
- `400 Bad Request` - Dados inválidos na requisição
- `401 Unauthorized` - Autenticação necessária ou token inválido
- `403 Forbidden` - Permissão insuficiente
- `404 Not Found` - Recurso não encontrado
- `409 Conflict` - Conflito de dados (ex: email já existe)
- `413 Payload Too Large` - Arquivo muito grande
- `415 Unsupported Media Type` - Tipo de arquivo não suportado
- `422 Unprocessable Entity` - Erro de validação
- `429 Too Many Requests` - Rate limit excedido

### Códigos de Erro do Servidor
- `500 Internal Server Error` - Erro interno do servidor
- `503 Service Unavailable` - Serviço temporariamente indisponível

---

## 🔧 Formato de Respostas de Erro

Todas as respostas de erro seguem um formato consistente:

```json
{
  "detail": "Descrição do erro",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-01T12:00:00Z",
  "path": "/menu-items",
  "method": "POST"
}
```

Para erros de validação (422):

```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "input": -5.0
    }
  ]
}
```

---

## 📝 Exemplos de Uso

### Fluxo Completo: Criar um Item com Imagem

```bash
# 1. Fazer login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Upload da imagem
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer eyJ..." \
  -F "file=@pizza.jpg"

# Response: {"filename": "pizza_20240101_120000.jpg", "url": "/static/images/pizza_20240101_120000.jpg"}

# 3. Criar item do menu
curl -X POST http://localhost:8000/menu-items \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pizza Quattro Stagioni",
    "description": "Pizza com presunto, cogumelos, alcachofras e azeitonas",
    "price": 42.90,
    "category": "pizzas",
    "available": true,
    "image_url": "/static/images/pizza_20240101_120000.jpg"
  }'
```

---

## 🛡️ Segurança

### Autenticação JWT
- Tokens com expiração configurável (padrão: 30 minutos)
- Algoritmo HS256 para assinatura
- Refresh tokens não implementados (por simplicidade)

### Rate Limiting
- Proteção contra ataques de força bruta
- Limites configuráveis por endpoint
- Storage em Redis para environments distribuídos

### Validação de Dados
- Validação rigorosa com Pydantic
- Sanitização de uploads de imagem
- Validação de tipos de arquivo

### Headers de Segurança
- CORS configurável para produção
- Headers de segurança automáticos

---

## 🚀 SDKs e Clientes

### JavaScript/TypeScript
```typescript
// Exemplo de cliente TypeScript
interface MenuAPI {
  login(email: string, password: string): Promise<AuthResponse>;
  getMenuItems(filters?: MenuFilters): Promise<MenuItemsResponse>;
  createMenuItem(item: CreateMenuItemRequest): Promise<MenuItem>;
  uploadImage(file: File): Promise<ImageUploadResponse>;
}

const api = new MenuAPIClient('http://localhost:8000');

// Login
const auth = await api.login('user@example.com', 'password');

// Buscar itens
const items = await api.getMenuItems({ category: 'pizzas' });

// Criar item
const newItem = await api.createMenuItem({
  name: 'Pizza Margherita',
  price: 35.90,
  category: 'pizzas'
});
```

### Python
```python
# Exemplo de cliente Python
import requests

class MenuAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
    
    def login(self, email: str, password: str):
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": email, "password": password}
        )
        self.token = response.json()["access_token"]
    
    def get_menu_items(self, **filters):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/menu-items",
            headers=headers,
            params=filters
        )
        return response.json()

# Uso
client = MenuAPIClient("http://localhost:8000")
client.login("user@example.com", "password")
items = client.get_menu_items(category="pizzas")
```

---

## 📞 Suporte

- **Documentação Interativa**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/detailed
- **Métricas**: http://localhost:8000/metrics

Para mais informações, consulte o README.md do projeto ou entre em contato com a equipe de desenvolvimento.

---

**✨ API pronta para produção com documentação completa!**
