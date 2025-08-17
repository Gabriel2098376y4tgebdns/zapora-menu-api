# 🚀 FastAPI Menu API - Checklist de Deploy

## ✅ Pré-Deploy Checklist

### 🔧 Configuração e Ambiente

- [ ] Todas as variáveis de ambiente de produção configuradas
- [ ] Arquivo `.env` criado com valores de produção
- [ ] `DATABASE_URL` apontando para PostgreSQL de produção
- [ ] `SECRET_KEY` gerado com segurança para produção
- [ ] `REDIS_URL` configurado (se usando cache Redis)
- [ ] Domínios CORS configurados corretamente
- [ ] Debug mode desabilitado (`DEBUG=false`)

### 🗃️ Banco de Dados

- [ ] PostgreSQL configurado e acessível
- [ ] Usuário de banco com permissões adequadas
- [ ] Backup do banco atual realizado
- [ ] Migrações testadas em ambiente de staging
- [ ] Índices de performance criados

### 🛡️ Segurança

- [ ] Certificados SSL/TLS configurados
- [ ] Headers de segurança habilitados
- [ ] Rate limiting configurado adequadamente
- [ ] Logs de auditoria funcionando
- [ ] Senhas padrão alteradas
- [ ] Acesso SSH restrito

### 🧪 Testes e Qualidade

- [ ] Todos os testes unitários passando
- [ ] Testes de integração executados
- [ ] Testes de performance realizados
- [ ] Validação de API com documentação
- [ ] Code coverage satisfatório (>80%)

### 📊 Monitoramento

- [ ] Prometheus configurado e funcionando
- [ ] Grafana dashboards importados
- [ ] Alertas configurados
- [ ] Logs centralizados
- [ ] Health checks funcionando

### 🐳 Containerização

- [ ] Dockerfile otimizado para produção
- [ ] Imagem Docker testada
- [ ] docker-compose.yml configurado
- [ ] Volumes de dados mapeados
- [ ] Networks isoladas

---

## 🚀 Comandos de Deploy

### Deploy com Docker Compose

```bash
# 1. Clone e configure
git clone <repo-url>
cd FastAPI

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com valores de produção

# 3. Execute deploy
./manage.sh docker

# 4. Verifique health checks
curl http://localhost:8000/health/detailed
```

### Deploy Manual

```bash
# 1. Setup do ambiente
./manage.sh setup

# 2. Configure produção
export ENVIRONMENT=production
export DEBUG=false
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export SECRET_KEY="your-production-secret"

# 3. Execute migrações
./manage.sh upgrade

# 4. Inicie produção
./manage.sh prod
```

### Deploy com Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-menu-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-menu-api
  template:
    metadata:
      labels:
        app: fastapi-menu-api
    spec:
      containers:
      - name: api
        image: menu-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 🔍 Verificações Pós-Deploy

### ✅ Verificação Imediata (0-5 minutos)

```bash
# 1. API respondendo
curl -f http://your-domain.com/healthz

# 2. Health check detalhado
curl http://your-domain.com/health/detailed

# 3. Documentação acessível
curl http://your-domain.com/docs

# 4. Autenticação funcionando
curl -X POST http://your-domain.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=your-password"

# 5. Métricas disponíveis
curl http://your-domain.com/metrics
```

### 🔎 Verificação Funcional (5-15 minutos)

```bash
# 1. Teste de CRUD completo
# Login
TOKEN=$(curl -X POST http://your-domain.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=your-password" \
  | jq -r '.access_token')

# Criar item
curl -X POST http://your-domain.com/menu-items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","price":10.99,"category":"test","available":true}'

# Listar itens
curl http://your-domain.com/menu-items

# 2. Teste de upload de imagem
curl -X POST http://your-domain.com/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-image.jpg"

# 3. Verificar logs de auditoria
curl -H "Authorization: Bearer $TOKEN" \
  http://your-domain.com/audit/logs
```

### 📊 Verificação de Performance (15-30 minutos)

```bash
# 1. Teste de carga básico
ab -n 1000 -c 10 http://your-domain.com/menu-items

# 2. Verificar métricas
curl http://your-domain.com/metrics | grep http_requests_total

# 3. Verificar rate limiting
for i in {1..10}; do
  curl -w "%{http_code}\n" http://your-domain.com/auth/login
done

# 4. Verificar cache (se Redis ativo)
curl http://your-domain.com/health/detailed | jq '.checks.redis'
```

---

## 🚨 Troubleshooting

### Problemas Comuns

#### API não responde
```bash
# Verificar logs
docker-compose logs api

# Verificar porta
netstat -tulpn | grep :8000

# Verificar processo
ps aux | grep uvicorn
```

#### Banco de dados não conecta
```bash
# Testar conexão
psql $DATABASE_URL -c "SELECT 1;"

# Verificar migrações
python -m my_menu_api.migration_utils current

# Verificar logs de banco
docker-compose logs postgres
```

#### Redis não conecta
```bash
# Testar Redis
redis-cli -u $REDIS_URL ping

# Verificar logs
docker-compose logs redis

# Verificar configuração
echo $REDIS_URL
```

#### Performance ruim
```bash
# Verificar métricas detalhadas
curl http://your-domain.com/metrics | grep -E "(http_request_duration|database_)"

# Verificar cache hit ratio
curl http://your-domain.com/health/detailed | jq '.checks.redis.hit_ratio'

# Verificar conexões de banco
curl http://your-domain.com/health/detailed | jq '.checks.database.pool_info'
```

### Rollback Procedure

```bash
# 1. Rollback da aplicação
docker-compose down
git checkout previous-stable-tag
docker-compose up -d

# 2. Rollback do banco (se necessário)
python -m my_menu_api.migration_utils downgrade previous_revision

# 3. Restaurar backup (último recurso)
pg_restore -d $DATABASE_URL backup_file.sql
```

---

## 📈 Monitoramento Contínuo

### Dashboards Grafana

1. **API Performance**
   - Request rate
   - Response time
   - Error rate
   - Active users

2. **Infrastructure**
   - CPU/Memory usage
   - Database connections
   - Cache hit ratio
   - Disk usage

3. **Business Metrics**
   - Menu items created
   - User registrations
   - Image uploads
   - Authentication attempts

### Alertas Recomendados

```yaml
# Prometheus alerts
groups:
- name: fastapi-menu-api
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 2m
    annotations:
      summary: "High error rate detected"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    annotations:
      summary: "High response time detected"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    annotations:
      summary: "Database is down"

  - alert: LowCacheHitRate
    expr: cache_hit_ratio < 0.7
    for: 10m
    annotations:
      summary: "Low cache hit rate"
```

---

## 📝 Documentação de Produção

### URLs Importantes

- **API**: https://api.your-domain.com
- **Docs**: https://api.your-domain.com/docs (admin only)
- **Health**: https://api.your-domain.com/health/detailed
- **Metrics**: https://api.your-domain.com/metrics
- **Grafana**: https://monitoring.your-domain.com:3000
- **Prometheus**: https://monitoring.your-domain.com:9090

### Contatos de Suporte

- **Desenvolvimento**: dev-team@your-company.com
- **DevOps**: devops@your-company.com
- **Emergência**: on-call@your-company.com

### Procedimentos de Manutenção

- **Backup diário**: 2:00 AM UTC
- **Atualizações**: Domingos às 3:00 AM UTC
- **Monitoramento**: 24/7 com alertas automatizados

---

**✅ Deploy checklist completo - Projeto pronto para produção!**
