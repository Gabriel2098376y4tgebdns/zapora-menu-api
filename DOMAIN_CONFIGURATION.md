# 🌐 Configuração de Domínio - FastAPI Menu API

## 📋 Visão Geral

Este guia explica como configurar um domínio personalizado para sua API FastAPI no Kubernetes com SSL automático usando cert-manager e Let's Encrypt.

### 🏗️ Arquitetura de Domínios

```
Produção:
├── api.meuprojeto.dev          # API principal
├── grafana.meuprojeto.dev      # Dashboard de monitoramento
└── prometheus.meuprojeto.dev   # Métricas (admin only)

Staging:
├── staging-api.meuprojeto.dev
├── staging-grafana.meuprojeto.dev
└── staging-prometheus.meuprojeto.dev

Desenvolvimento:
├── dev-api.meuprojeto.dev
├── dev-grafana.meuprojeto.dev
└── dev-prometheus.meuprojeto.dev
```

---

## 🔧 1. Configuração do Domínio

### 📝 Registrar Domínio

1. **Registre um domínio** (ex: `meuprojeto.dev`)
   - Recomendado: Cloudflare, Namecheap, GoDaddy
   - Para testes: Use serviços gratuitos como Freenom ou nip.io

2. **Configure DNS no Cloudflare** (Recomendado)
   
   Adicione os seguintes registros DNS:

   ```
   Tipo  | Nome                      | Destino            | TTL
   ------|---------------------------|--------------------|---------
   A     | api.meuprojeto.dev        | YOUR_CLUSTER_IP    | Auto
   A     | grafana.meuprojeto.dev    | YOUR_CLUSTER_IP    | Auto
   A     | prometheus.meuprojeto.dev | YOUR_CLUSTER_IP    | Auto
   A     | staging-api.meuprojeto.dev| YOUR_CLUSTER_IP    | Auto
   A     | dev-api.meuprojeto.dev    | YOUR_CLUSTER_IP    | Auto
   CNAME | *.meuprojeto.dev          | meuprojeto.dev     | Auto
   ```

### 🔍 Descobrir IP do Cluster

#### Para LoadBalancer (GKE, EKS, AKS):
```bash
# Obter IP externo do LoadBalancer
kubectl get service ingress-nginx-controller -n ingress-nginx

# Output esperado:
# NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)
# ingress-nginx-controller   LoadBalancer   10.0.0.100      203.0.113.10    80:32000/TCP,443:32001/TCP
```

#### Para NodePort (Minikube, Bare Metal):
```bash
# Obter IP dos nodes
kubectl get nodes -o wide

# Obter porta do NodePort
kubectl get service ingress-nginx-controller -n ingress-nginx
```

#### Para Minikube (Desenvolvimento):
```bash
# Obter IP do Minikube
minikube ip

# Habilitar tunnel para LoadBalancer
minikube tunnel
```

---

## 🔒 2. Configuração SSL com cert-manager

### 📦 Instalação do cert-manager

```bash
# Instalar cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Verificar instalação
kubectl get pods --namespace cert-manager

# Aguardar todos os pods estarem Running
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
```

### 🔑 Configurar Let's Encrypt

Os ClusterIssuers já estão configurados nos manifests:

```yaml
# Produção (certificados válidos)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@meuprojeto.dev  # MUDE PARA SEU EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx

# Staging (para testes)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@meuprojeto.dev  # MUDE PARA SEU EMAIL
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

### ✏️ Personalizar Configuração

1. **Edite o email nos ClusterIssuers:**
   ```bash
   # Editar arquivo de ingress
   vim k8s/base/ingress.yaml
   
   # Substituir 'admin@meuprojeto.dev' pelo seu email
   ```

2. **Edite os domínios nos Ingress:**
   ```bash
   # Editar configurações de ambiente
   vim k8s/environments/prod/kustomization.yaml
   vim k8s/environments/staging/kustomization.yaml
   vim k8s/environments/dev/kustomization.yaml
   
   # Substituir 'meuprojeto.dev' pelo seu domínio
   ```

---

## 🚀 3. Deploy com Domínio Personalizado

### 🔄 Deploy Completo

```bash
# 1. Configurar prerequisites
./deploy.sh setup

# 2. Build e push da imagem
./deploy.sh prod build

# 3. Deploy em produção
./deploy.sh prod deploy

# 4. Verificar status
./deploy.sh prod status
```

### 🔍 Verificar Certificados SSL

```bash
# Verificar certificados
kubectl get certificates -n fastapi-menu-api-prod

# Ver detalhes do certificado
kubectl describe certificate meuprojeto-tls -n fastapi-menu-api-prod

# Verificar certificados issued
kubectl get certificaterequests -n fastapi-menu-api-prod
```

### 🧪 Testar Conectividade

```bash
# Testar API
curl -I https://api.meuprojeto.dev/healthz

# Testar redirecionamento HTTP → HTTPS
curl -I http://api.meuprojeto.dev/healthz

# Verificar certificado SSL
openssl s_client -connect api.meuprojeto.dev:443 -servername api.meuprojeto.dev
```

---

## 🛠️ 4. Troubleshooting

### ❌ Problemas Comuns

#### 🔴 Certificado não emitido
```bash
# Verificar eventos do cert-manager
kubectl describe certificaterequest -n fastapi-menu-api-prod

# Ver logs do cert-manager
kubectl logs -n cert-manager deployment/cert-manager

# Verificar challenges
kubectl get challenges -n fastapi-menu-api-prod
```

**Soluções:**
- Verificar se DNS aponta para o IP correto
- Confirmar que porta 80 está acessível (HTTP-01 challenge)
- Verificar rate limits do Let's Encrypt

#### 🔴 DNS não resolve
```bash
# Testar resolução DNS
nslookup api.meuprojeto.dev
dig api.meuprojeto.dev

# Verificar propagação DNS
curl "https://dns-checker.org/api/dns-checker?domain=api.meuprojeto.dev&type=A"
```

**Soluções:**
- Aguardar propagação DNS (até 48h)
- Verificar configuração no provedor DNS
- Usar DNS público: 8.8.8.8, 1.1.1.1

#### 🔴 Ingress não funciona
```bash
# Verificar nginx-ingress
kubectl get pods -n ingress-nginx

# Ver logs do ingress controller
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Verificar configuração do Ingress
kubectl describe ingress fastapi-menu-api-ingress -n fastapi-menu-api-prod
```

---

## 🌍 5. Configurações Específicas por Provedor

### ☁️ Google Cloud (GKE)

```bash
# Reservar IP estático
gcloud compute addresses create fastapi-menu-api-ip --global

# Obter IP reservado
gcloud compute addresses describe fastapi-menu-api-ip --global

# Configurar LoadBalancer para usar IP estático
kubectl patch service ingress-nginx-controller -n ingress-nginx -p '{"spec":{"loadBalancerIP":"YOUR_STATIC_IP"}}'
```

### ☁️ AWS (EKS)

```bash
# Instalar AWS Load Balancer Controller
kubectl apply -f https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.6.0/v2_6_0_full.yaml

# Anotar LoadBalancer para usar NLB
kubectl annotate service ingress-nginx-controller -n ingress-nginx service.beta.kubernetes.io/aws-load-balancer-type=nlb
```

### ☁️ Azure (AKS)

```bash
# Criar IP público estático
az network public-ip create \
    --resource-group MC_myResourceGroup_myAKSCluster_eastus \
    --name myAKSPublicIP \
    --sku Standard \
    --allocation-method static

# Aplicar IP ao LoadBalancer
kubectl patch service ingress-nginx-controller -n ingress-nginx -p '{"spec":{"loadBalancerIP":"YOUR_STATIC_IP"}}'
```

### 🏠 Bare Metal / On-Premises

```bash
# Usar NodePort
kubectl patch service ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"NodePort"}}'

# Configurar proxy reverso (nginx, HAProxy)
# Exemplo nginx:
server {
    listen 80;
    server_name *.meuprojeto.dev;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name *.meuprojeto.dev;
    
    location / {
        proxy_pass http://NODE_IP:NODE_PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 6. Monitoramento de Domínio

### 🔍 Scripts de Verificação

```bash
#!/bin/bash
# check_domains.sh - Verificar saúde dos domínios

DOMAINS=("api.meuprojeto.dev" "grafana.meuprojeto.dev" "prometheus.meuprojeto.dev")

for domain in "${DOMAINS[@]}"; do
    echo "Checking $domain..."
    
    # Check HTTP status
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain/healthz" || echo "000")
    
    # Check SSL certificate
    cert_days=$(echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | openssl x509 -noout -dates | grep "notAfter" | cut -d= -f2)
    
    echo "  HTTP Status: $status"
    echo "  SSL Expires: $cert_days"
    echo "---"
done
```

### 📈 Alertas de Monitoramento

```yaml
# prometheus-domain-alerts.yaml
groups:
- name: domain-monitoring
  rules:
  - alert: DomainDown
    expr: probe_success{job="blackbox"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Domain {{ $labels.instance }} is down"

  - alert: SSLCertificateExpiring
    expr: probe_ssl_earliest_cert_expiry{job="blackbox"} - time() < 86400 * 7
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "SSL certificate for {{ $labels.instance }} expires in less than 7 days"
```

---

## ✅ 7. Checklist Final

### 🔍 Pré-Deploy
- [ ] Domínio registrado e DNS configurado
- [ ] IP do cluster identificado e configurado no DNS
- [ ] cert-manager instalado no cluster
- [ ] nginx-ingress controller instalado
- [ ] Email configurado nos ClusterIssuers

### 🚀 Deploy
- [ ] Manifests personalizados com seu domínio
- [ ] Deploy executado com sucesso
- [ ] Certificados SSL emitidos
- [ ] DNS resolvendo corretamente
- [ ] HTTPS funcionando (redirecionamento HTTP → HTTPS)

### ✅ Pós-Deploy
- [ ] API respondendo em https://api.meuprojeto.dev
- [ ] Grafana acessível em https://grafana.meuprojeto.dev
- [ ] Certificados válidos (sem warnings no browser)
- [ ] Monitoramento configurado
- [ ] Backups automatizados funcionando

---

**🎯 Domínio configurado com sucesso!** Sua API agora está acessível via HTTPS com certificados SSL automáticos.

Para suporte, verifique os logs:
```bash
# Logs da aplicação
./deploy.sh prod logs

# Status do sistema
./deploy.sh prod status
```
