# 🚀 FastAPI Menu API - Deploy Kubernetes Completo

## 🎯 Visão Geral

Infraestrutura completa de produção para FastAPI Menu API usando Kubernetes, com SSL automático, monitoramento, backup e segregação de ambientes.

### 🏗️ Arquitetura da Solução

```
🌐 Internet (HTTPS)
    ↓
🔒 Let's Encrypt SSL Certificates
    ↓
🌉 Nginx Ingress Controller
    ↓
┌─────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                    │
├─────────────────┬─────────────────┬─────────────────────┤
│   Development   │     Staging     │     Production      │
│   Namespace     │    Namespace    │     Namespace       │
├─────────────────┼─────────────────┼─────────────────────┤
│ 🚀 FastAPI (1x) │ 🚀 FastAPI (2x) │ 🚀 FastAPI (5x)     │
│ 🗃️ PostgreSQL   │ 🗃️ PostgreSQL   │ 🗃️ PostgreSQL       │
│ ⚡ Redis        │ ⚡ Redis        │ ⚡ Redis            │
│ 📊 Prometheus   │ 📊 Prometheus   │ 📊 Prometheus       │
│ 📈 Grafana      │ 📈 Grafana      │ 📈 Grafana          │
│ 💾 Backup       │ 💾 Backup       │ 💾 Backup           │
└─────────────────┴─────────────────┴─────────────────────┘
```

---

## 🗂️ Estrutura do Projeto

```
k8s/
├── base/                           # Manifests base (Kustomize)
│   ├── namespace.yaml              # Namespaces por ambiente
│   ├── secrets.yaml                # Credenciais (PostgreSQL, JWT, Redis)
│   ├── configmap.yaml              # Configurações da aplicação
│   ├── postgres.yaml               # PostgreSQL StatefulSet + PVC
│   ├── redis.yaml                  # Redis Deployment + PVC
│   ├── fastapi.yaml                # FastAPI Deployment + Service
│   ├── prometheus.yaml             # Prometheus + Configuração
│   ├── grafana.yaml                # Grafana + Dashboards
│   ├── ingress.yaml                # Ingress + SSL + Security
│   ├── backup.yaml                 # Backup automatizado (CronJob)
│   └── kustomization.yaml          # Kustomize base
├── environments/                   # Configurações por ambiente
│   ├── dev/kustomization.yaml      # Desenvolvimento (1 replica)
│   ├── staging/kustomization.yaml  # Staging (2 replicas)
│   └── prod/kustomization.yaml     # Produção (5 replicas)
deploy.sh                           # Script de deploy automatizado
DOMAIN_CONFIGURATION.md             # Guia de configuração de domínio
```

---

## 🚀 1. Início Rápido

### 📋 Pré-requisitos

```bash
# Verificar ferramentas necessárias
kubectl version --client
docker --version
helm version  # Opcional

# Verificar conexão com cluster
kubectl cluster-info
```

### ⚡ Deploy em 3 Comandos

```bash
# 1. Setup de prerequisites (cert-manager, nginx-ingress)
./deploy.sh setup

# 2. Deploy em desenvolvimento
./deploy.sh dev deploy

# 3. Verificar status
./deploy.sh dev status
```

### 🌐 Acessar Aplicação

```bash
# API Documentation
open https://dev-api.meuprojeto.dev/docs

# Monitoring Dashboard
open https://dev-grafana.meuprojeto.dev

# Health Check
curl https://dev-api.meuprojeto.dev/healthz
```

---

## 🔧 2. Configuração Detalhada

### 🔑 Secrets e Configurações

#### Editar Credenciais de Produção:
```bash
# Gerar nova SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Editar secrets
vim k8s/base/secrets.yaml

# Importante: As secrets estão em Base64!
echo -n "nova-senha-super-secreta" | base64
```

#### Configurar Domínio:
```bash
# 1. Editar domínios nos ambientes
vim k8s/environments/prod/kustomization.yaml
vim k8s/environments/staging/kustomization.yaml
vim k8s/environments/dev/kustomization.yaml

# 2. Configurar email para Let's Encrypt
vim k8s/base/ingress.yaml
# Alterar: email: admin@meuprojeto.dev
```

### 🗃️ PostgreSQL com Alta Disponibilidade

#### Características:
- **StatefulSet**: Garante ordem de inicialização
- **PVC**: Volume persistente de 10Gi (dev) até 50Gi (prod)
- **Health Checks**: Liveness e Readiness probes
- **Security**: Usuário não-root, fsGroup configurado
- **Backup**: Automatizado via CronJob

#### Verificar PostgreSQL:
```bash
# Status do StatefulSet
kubectl get statefulset postgres -n fastapi-menu-api-dev

# Logs do PostgreSQL
kubectl logs -f postgres-0 -n fastapi-menu-api-dev

# Conectar ao banco (debug)
kubectl exec -it postgres-0 -n fastapi-menu-api-dev -- psql -U postgres -d menuapi
```

### ⚡ Redis para Cache

#### Características:
- **Persistência**: AOF habilitado + snapshots
- **Performance**: Configurado para alta performance
- **Health Checks**: TCP e comando PING
- **Volume**: 2Gi de storage

#### Verificar Redis:
```bash
# Status do Redis
kubectl get deployment redis -n fastapi-menu-api-dev

# Testar conexão
kubectl exec -it deployment/redis -n fastapi-menu-api-dev -- redis-cli ping
```

---

## 🛡️ 3. Segurança e SSL

### 🔒 SSL Automático com Let's Encrypt

#### Características:
- **cert-manager**: Gerenciamento automático de certificados
- **Let's Encrypt**: Certificados gratuitos e válidos
- **HTTP-01 Challenge**: Validação automática via HTTP
- **Renovação Automática**: Certificados renovados automaticamente

#### Configuração SSL:
```yaml
# ClusterIssuer para produção
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@meuprojeto.dev  # SEU EMAIL AQUI
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

#### Verificar Certificados:
```bash
# Status dos certificados
kubectl get certificates -n fastapi-menu-api-prod

# Detalhes do certificado
kubectl describe certificate meuprojeto-tls -n fastapi-menu-api-prod

# Testar SSL
curl -I https://api.meuprojeto.dev/healthz
```

### 🛡️ Headers de Segurança

Configurados automaticamente no Ingress:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy`

---

## 📊 4. Monitoramento e Observabilidade

### 📈 Stack de Monitoramento

#### Prometheus:
- **Métricas**: API, banco, Redis, Kubernetes
- **Alertas**: Configurados para alta disponibilidade
- **Retenção**: 30 dias de dados
- **Storage**: 5Gi de volume persistente

#### Grafana:
- **Dashboards**: Pré-configurados para FastAPI
- **DataSource**: Prometheus automático
- **Alerting**: Integrado com Prometheus
- **Auth**: Admin/admin123 (alterar em produção)

### 📊 Dashboards Disponíveis

```bash
# Acessar Grafana
open https://grafana.meuprojeto.dev

# Dashboards inclusos:
# - FastAPI Performance
# - PostgreSQL Metrics
# - Redis Performance
# - Kubernetes Resources
# - Application Health
```

### 🔔 Alertas Configurados

- **HighErrorRate**: Taxa de erro > 10%
- **HighResponseTime**: P95 > 2 segundos
- **DatabaseDown**: PostgreSQL não responde
- **RedisDown**: Redis não responde
- **APIDown**: FastAPI não responde

---

## 💾 5. Estratégia de Backup

### 🔄 Backup Automatizado

#### Características:
- **Frequência**: Diário às 2h da manhã
- **Retenção**: 30 dias
- **Compressão**: gzip automático
- **Metadados**: JSON com informações do backup
- **Storage**: Volume persistente dedicado

#### Scripts Disponíveis:
```bash
# Backup manual
./deploy.sh prod backup

# Listar backups
kubectl exec -n fastapi-menu-api-prod deployment/postgres-backup -- /scripts/list_backups.sh

# Restaurar backup
./deploy.sh prod restore
```

#### Verificar Backups:
```bash
# Status do CronJob
kubectl get cronjob postgres-backup -n fastapi-menu-api-prod

# Logs do último backup
kubectl logs -l app=postgres-backup -n fastapi-menu-api-prod

# Listar arquivos de backup
kubectl exec -n fastapi-menu-api-prod \
  $(kubectl get pod -l app=postgres-backup -o jsonpath='{.items[0].metadata.name}' -n fastapi-menu-api-prod) \
  -- ls -la /backup/
```

---

## 🌍 6. Ambientes e Deploy

### 🔄 Estratégia de Deploy

#### Desenvolvimento:
- **Replicas**: 1 FastAPI pod
- **Resources**: Mínimos (128Mi-256Mi)
- **SSL**: Let's Encrypt Staging
- **Domínio**: dev-api.meuprojeto.dev

#### Staging:
- **Replicas**: 2 FastAPI pods
- **Resources**: Médios (256Mi-512Mi)
- **SSL**: Let's Encrypt Staging
- **Domínio**: staging-api.meuprojeto.dev

#### Produção:
- **Replicas**: 5 FastAPI pods
- **Resources**: Altos (512Mi-1Gi)
- **SSL**: Let's Encrypt Production
- **Domínio**: api.meuprojeto.dev

### 🚀 Comandos de Deploy

```bash
# Deploy em desenvolvimento
./deploy.sh dev deploy

# Deploy em staging
./deploy.sh staging deploy

# Deploy em produção (com confirmação)
./deploy.sh prod deploy

# Verificar status de qualquer ambiente
./deploy.sh [env] status

# Ver logs em tempo real
./deploy.sh [env] logs

# Deletar deployment (cuidado!)
./deploy.sh [env] delete
```

---

## 🔧 7. Troubleshooting

### ❌ Problemas Comuns

#### 🔴 Pods não iniciam
```bash
# Verificar status dos pods
kubectl get pods -n fastapi-menu-api-dev

# Ver logs detalhados
kubectl describe pod <pod-name> -n fastapi-menu-api-dev

# Ver logs da aplicação
kubectl logs <pod-name> -n fastapi-menu-api-dev
```

#### 🔴 Banco de dados não conecta
```bash
# Verificar PostgreSQL
kubectl exec -it postgres-0 -n fastapi-menu-api-dev -- pg_isready

# Testar conexão manual
kubectl run psql-test --rm -i --restart=Never --image=postgres:15-alpine -- psql postgresql://postgres:postgres123@postgres-service:5432/menuapi -c "SELECT 1;"
```

#### 🔴 SSL/Certificados
```bash
# Verificar cert-manager
kubectl get pods -n cert-manager

# Ver challenges do Let's Encrypt
kubectl get challenges -n fastapi-menu-api-dev

# Logs do cert-manager
kubectl logs -n cert-manager deployment/cert-manager
```

#### 🔴 Ingress não funciona
```bash
# Verificar nginx-ingress
kubectl get pods -n ingress-nginx

# Ver configuração do Ingress
kubectl describe ingress fastapi-menu-api-ingress -n fastapi-menu-api-dev

# Logs do ingress controller
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### 🔧 Comandos Úteis

```bash
# Ver todos os recursos
kubectl get all -n fastapi-menu-api-dev

# Ver eventos recentes
kubectl get events -n fastapi-menu-api-dev --sort-by='.lastTimestamp'

# Fazer port-forward para debug
kubectl port-forward service/fastapi-menu-api-service 8000:80 -n fastapi-menu-api-dev

# Executar comando dentro do pod
kubectl exec -it <pod-name> -n fastapi-menu-api-dev -- /bin/bash

# Ver uso de recursos
kubectl top pods -n fastapi-menu-api-dev
kubectl top nodes
```

---

## 📈 8. Escalabilidade e Performance

### 🔄 Horizontal Pod Autoscaler (HPA)

```yaml
# hpa.yaml - Adicionar aos manifests se necessário
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: fastapi-menu-api-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-menu-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 📊 Métricas de Performance

- **Response Time**: P50, P95, P99
- **Throughput**: Requests/second
- **Error Rate**: 4xx, 5xx errors
- **Resource Usage**: CPU, Memory, Disk
- **Database**: Connections, Query time
- **Cache**: Hit ratio, Response time

---

## ✅ 9. Checklist de Produção

### 🔒 Segurança
- [ ] Secrets configuradas com valores únicos
- [ ] SSL/TLS configurado e funcionando
- [ ] Headers de segurança habilitados
- [ ] Network policies configuradas (se necessário)
- [ ] RBAC configurado adequadamente

### 📊 Monitoramento
- [ ] Prometheus coletando métricas
- [ ] Grafana com dashboards configurados
- [ ] Alertas configurados e testados
- [ ] Logs centralizados funcionando
- [ ] Health checks respondendo

### 💾 Backup
- [ ] Backup automatizado configurado
- [ ] Retenção de backups adequada
- [ ] Restore testado e funcionando
- [ ] Volumes persistentes configurados
- [ ] Políticas de snapshot (se cloud)

### 🚀 Deploy
- [ ] CI/CD pipeline configurado
- [ ] Rollback strategy definida
- [ ] Blue/Green ou Rolling deploy
- [ ] Resource limits configurados
- [ ] Auto-scaling configurado

### 🌐 Networking
- [ ] Domínio configurado e resolvendo
- [ ] Load balancer configurado
- [ ] CDN configurado (se necessário)
- [ ] Rate limiting habilitado
- [ ] CORS configurado adequadamente

---

## 🎯 10. Próximos Passos

### 🔮 Melhorias Futuras

1. **Service Mesh** (Istio/Linkerd)
   - Traffic management avançado
   - Security policies granulares
   - Observability nativa

2. **GitOps** (ArgoCD/Flux)
   - Deploy automatizado via Git
   - Rollback automático
   - Config drift detection

3. **Chaos Engineering**
   - Chaos Monkey para Kubernetes
   - Teste de resiliência
   - Disaster recovery

4. **Multi-Region**
   - Deploy em múltiplas regiões
   - Disaster recovery
   - Low latency global

---

## 📞 Suporte e Recursos

### 📚 Documentação
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Prometheus Operator](https://prometheus-operator.dev/)

### 🛠️ Ferramentas Úteis
- **K9s**: Terminal UI para Kubernetes
- **Helm**: Package manager para Kubernetes  
- **Kustomize**: Template-free customization
- **Skaffold**: Continuous development para Kubernetes

### 🆘 Comandos de Emergência

```bash
# Restart completo da aplicação
kubectl rollout restart deployment/fastapi-menu-api -n fastapi-menu-api-prod

# Escalar rapidamente
kubectl scale deployment fastapi-menu-api --replicas=10 -n fastapi-menu-api-prod

# Backup de emergência
./deploy.sh prod backup

# Verificar saúde geral
./deploy.sh prod status
```

---

**🎉 Infraestrutura Kubernetes pronta para produção!**

Sua FastAPI Menu API agora tem uma infraestrutura robusta, escalável e segura, pronta para suportar cargas de trabalho de produção com alta disponibilidade e observabilidade completa.

Para deploy completo, execute:
```bash
./deploy.sh setup && ./deploy.sh prod deploy
```
