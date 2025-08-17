# 🏗️ Zapora - Architecture Diagrams

## 📊 System Architecture Overview

```
                                    Internet
                                        │
                                        ▼
                          ┌─────────────────────────────┐
                          │      Load Balancer          │
                          │    (Nginx Ingress)          │
                          │  SSL Termination + WAF      │
                          └─────────────┬───────────────┘
                                        │
                            ┌───────────┴───────────┐
                            │                       │
                            ▼                       ▼
                    ┌───────────────┐       ┌───────────────┐
                    │   FastAPI     │       │   FastAPI     │
                    │   Pod 1       │  ...  │   Pod N       │
                    │ (Auto-scaling)│       │ (Auto-scaling)│
                    └───────┬───────┘       └───────┬───────┘
                            │                       │
                            └───────────┬───────────┘
                                        │
                        ┌───────────────┼───────────────┐
                        │               │               │
                        ▼               ▼               ▼
                ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                │ PostgreSQL  │ │    Redis    │ │ Prometheus  │
                │  (Primary)  │ │   Cluster   │ │  + Grafana  │
                │             │ │  (Cache)    │ │(Monitoring) │
                └─────────────┘ └─────────────┘ └─────────────┘
                        │
                        ▼
                ┌─────────────┐
                │ PostgreSQL  │
                │ (Replica)   │
                │ (Read-Only) │
                └─────────────┘
```

## 🔄 Request Flow Diagram

```
User Request Journey
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  📱 Client App                                                  │
│  ├─ POST /auth/login                                           │
│  ├─ GET /menu-items                                            │
│  └─ POST /orders                                               │
│                                                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS Request
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  🌐 Nginx Ingress Controller                                   │
│  ├─ Rate Limiting (100 req/min)                               │
│  ├─ SSL Termination (Let's Encrypt)                           │
│  ├─ Security Headers (HSTS, CSP, XSS)                         │
│  └─ Load Balancing (Round Robin)                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP Request
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  🚀 FastAPI Application                                        │
│  ├─ JWT Authentication Middleware                              │
│  ├─ Request Validation (Pydantic)                             │
│  ├─ Business Logic Processing                                  │
│  └─ Response Serialization                                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │ Cache Check │ DB Query    │ Metrics
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Redis    │ │ PostgreSQL  │ │ Prometheus  │
│   Cluster   │ │   Primary   │ │  Metrics    │
│             │ │             │ │ Collection  │
│ ├─ Sessions │ │ ├─ Users    │ │             │
│ ├─ Cache    │ │ ├─ Orders   │ │ ├─ Latency │
│ └─ Queues   │ │ └─ Menus    │ │ ├─ Errors  │
└─────────────┘ └─────────────┘ │ └─ Traffic │
                                └─────────────┘
```

## 🔐 Security Architecture

```
Security Layers (Defense in Depth)
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security                                     │
│  ├─ Firewall Rules                                            │
│  ├─ VPN Access Only                                           │
│  └─ Private Subnets                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│  Layer 2: Application Gateway                                  │
│  ├─ WAF (Web Application Firewall)                            │
│  ├─ DDoS Protection                                           │
│  ├─ Rate Limiting                                             │
│  └─ IP Whitelisting                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│  Layer 3: Application Security                                 │
│  ├─ JWT Authentication (HS256)                                │
│  ├─ RBAC (Role-Based Access Control)                          │
│  ├─ Input Validation (Pydantic)                               │
│  ├─ SQL Injection Protection (ORM)                            │
│  └─ OWASP Security Headers                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│  Layer 4: Data Security                                        │
│  ├─ Encryption at Rest (AES-256)                              │
│  ├─ Encryption in Transit (TLS 1.3)                           │
│  ├─ Password Hashing (Bcrypt)                                 │
│  ├─ Secrets Management (K8s Secrets)                          │
│  └─ Audit Logging                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 📈 Auto-Scaling Strategy

```
Horizontal Pod Autoscaler (HPA) Flow
┌─────────────────────────────────────────────────────────────────┐
│                     Metrics Collection                         │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Pod 1     │    │   Pod 2     │    │   Pod N     │         │
│  │ CPU: 45%    │    │ CPU: 78%    │    │ CPU: 92%    │         │
│  │ Memory: 60% │    │ Memory: 70% │    │ Memory: 85% │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────┬───────────────────────────────────────────────────┘
              │ Metrics Aggregation
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 HPA Controller Decision                         │
│                                                                 │
│  Average CPU: 72% (Target: 70%)                               │
│  Average Memory: 71% (Target: 75%)                            │
│                                                                 │
│  Decision: SCALE UP (CPU threshold exceeded)                   │
└─────────────┬───────────────────────────────────────────────────┘
              │ Scale Decision
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Scaling Action                               │
│                                                                 │
│  Current Replicas: 3                                          │
│  Target Replicas: 5                                           │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Pod 1     │ │   Pod 2     │ │   Pod 3     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ← New Pods                   │
│  │   Pod 4     │ │   Pod 5     │                              │
│  │ (Starting)  │ │ (Starting)  │                              │
│  └─────────────┘ └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## 💾 Backup & Disaster Recovery

```
Backup Strategy & Recovery Process
┌─────────────────────────────────────────────────────────────────┐
│                     Production Data                             │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ PostgreSQL  │    │    Redis    │    │  File Store │         │
│  │  Primary    │    │   Cluster   │    │   (Images)  │         │
│  │             │    │             │    │             │         │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘         │
└─────────┼─────────────────┼─────────────────┼─────────────────┘
          │                 │                 │
          │ Daily           │ Hourly          │ Real-time
          │ Full Backup     │ Incremental     │ Replication
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backup Storage                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   AWS S3    │    │   Azure     │    │   GCS       │         │
│  │ (Primary)   │    │  (Secondary)│    │ (Archive)   │         │
│  │             │    │             │    │             │         │
│  │ • 30 days   │    │ • 90 days   │    │ • 7 years   │         │
│  │ • Hot       │    │ • Warm      │    │ • Cold      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ Disaster Recovery
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Recovery Process                               │
│                                                                 │
│  RTO (Recovery Time Objective): < 5 minutes                   │
│  RPO (Recovery Point Objective): < 1 minute                   │
│                                                                 │
│  Step 1: Automated Failover Detection                         │
│  Step 2: Backup Selection & Validation                        │
│  Step 3: Infrastructure Provisioning                          │
│  Step 4: Data Restoration                                     │
│  Step 5: Service Health Verification                          │
│  Step 6: Traffic Routing                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Monitoring & Observability

```
Observability Stack (Three Pillars)
┌─────────────────────────────────────────────────────────────────┐
│                     📊 METRICS                                 │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Application │    │    System   │    │  Business   │         │
│  │   Metrics   │    │   Metrics   │    │   Metrics   │         │
│  │             │    │             │    │             │         │
│  │ • Latency   │    │ • CPU/RAM   │    │ • Orders    │         │
│  │ • Errors    │    │ • Network   │    │ • Revenue   │         │
│  │ • Requests  │    │ • Disk I/O  │    │ • Users     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────┬───────────────────────────────────────────────────┘
              │ Prometheus Collection
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     📝 LOGS                                    │
│                                                                 │
│  Application Logs → Structured JSON → ELK Stack               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    Error    │    │   Access    │    │    Audit    │         │
│  │    Logs     │    │    Logs     │    │    Logs     │         │
│  │             │    │             │    │             │         │
│  │ • Stack     │    │ • Requests  │    │ • User      │         │
│  │   Traces    │    │ • Response  │    │   Actions   │         │
│  │ • Context   │    │   Times     │    │ • Security  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────┬───────────────────────────────────────────────────┘
              │ Centralized Logging
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     🔍 TRACES                                  │
│                                                                 │
│  Request Journey Tracking → Jaeger                            │
│                                                                 │
│  User Request → Ingress → FastAPI → Database → Response       │
│       │            │         │         │          │           │
│       └────────────┴─────────┴─────────┴──────────┘           │
│                    Distributed Tracing                         │
│                                                                 │
│  • Request ID Correlation                                      │
│  • Performance Bottlenecks                                    │
│  • Error Propagation                                          │
│  • Service Dependencies                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 CI/CD Pipeline

```
Continuous Integration / Continuous Deployment
┌─────────────────────────────────────────────────────────────────┐
│                   Code Commit (Git)                            │
│                                                                 │
│   Developer → Git Push → GitHub/GitLab                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Webhook Trigger
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CI Pipeline (GitHub Actions)                   │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │    Build    │ │    Test     │ │   Security  │ │  Package  │ │
│  │             │ │             │ │    Scan     │ │           │ │
│  │ • Install   │ │ • Unit      │ │ • SAST      │ │ • Docker  │ │
│  │   Deps      │ │ • Integration│ │ • Dependency│ │   Build   │ │
│  │ • Lint      │ │ • Coverage  │ │   Audit     │ │ • Push    │ │
│  │ • Type      │ │ • Load      │ │ • OWASP     │ │   Registry│ │
│  │   Check     │ │   Test      │ │   ZAP       │ │           │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Success Gate
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                CD Pipeline (ArgoCD / Flux)                     │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Deploy    │ │   Health    │ │  Smoke      │ │ Production│ │
│  │  Staging    │ │   Check     │ │   Test      │ │  Deploy   │ │
│  │             │ │             │ │             │ │           │ │
│  │ • K8s       │ │ • Readiness │ │ • API       │ │ • Rolling │ │
│  │   Apply     │ │ • Liveness  │ │   Tests     │ │   Update  │ │
│  │ • Database  │ │ • Database  │ │ • E2E       │ │ • Blue/   │ │
│  │   Migrate   │ │   Health    │ │   Tests     │ │   Green   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```
