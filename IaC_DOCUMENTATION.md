# Infrastructure as Code (IaC) & Deployment Guide

**Last Updated**: April 20, 2026  
**Status**: Production-Ready

---

## Overview

This document describes the Infrastructure as Code (IaC) approach for the AI Agent system, covering deployment options from local Docker to cloud platforms.

---

## Architecture Levels

### Level 1: Local Development
**Technology**: Docker + Docker Compose (standalone)  
**Cost**: Free  
**Complexity**: Low  
**Use Case**: Development, testing, demos

### Level 2: Containerized Multi-Service
**Technology**: Docker Compose with service separation  
**Cost**: Free  
**Complexity**: Medium  
**Use Case**: Local full-stack testing, optional monitoring

### Level 3: Cloud Deployment
**Platforms**: Render.com, Railway.app, AWS  
**Cost**: $0-50/month  
**Complexity**: Medium-High  
**Use Case**: Production, interviews, live demos

---

## Current Implementation: docker-compose.yml

The project uses **multi-profile Docker Compose** for flexible deployment:

### Core Services (Always Running)

```yaml
services:
  chroma:          # Vector database for RAG
  api:             # FastAPI backend
```

### Why This Architecture

| Component | Purpose | Rationale |
|-----------|---------|-----------|
| **Chroma** | Vector store | Separated for scalability; can be hosted externally |
| **API** | Business logic | Stateless FastAPI enables horizontal scaling |
| **SQLite** | Conversation history | Local persistence for session data and metrics |
| **Structured Logging** | Observability | JSON logs for easy parsing and analysis |

---

## Deployment Options

### Option A: Local Docker Compose (Recommended)

```bash
# 1. Build and run all services
docker-compose up --build

# 2. In another terminal, test
curl http://localhost:8000/health

# 3. Access Chroma
curl http://localhost:8001/api/v1/heartbeat
```

**Pros**: 
- Zero cost
- Full-stack in one command
- Perfect for local testing and development

**Cons**: 
- Not suitable for high-traffic production without scaling
- Single-machine bottleneck

---

### Option C: Render.com Deployment (Recommended for Quick Setup)

**Time**: 5-10 minutes  
**Cost**: Free (with generous limits)

#### Step 1: Create Render Account
Visit https://render.com and sign up

#### Step 2: Create Web Service
1. New → Web Service
2. Connect your GitHub repo
3. Configure:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port 8000
   Environment:
     - DATABASE_PATH=/var/data/conversations.db
     - LOG_FILE=/var/log/app.log
     - OPENROUTER_API_KEY=<your_key>
   ```

#### Step 3: Deploy
```bash
git push origin main
# Render automatically builds and deploys
```

#### Step 4: Access Live
```
https://<your-service>.onrender.com/health
```

**Pros**:
- No infrastructure management
- Automatic deployment from Git
- Free tier very generous
- Easy to share live links

**Cons**:
- Spin-down after inactivity (cold starts)
- Limited compute
- Not suitable for high-traffic production

---

### Option D: Railway.app Deployment

**Time**: 5-10 minutes  
**Cost**: Free (5$/month credit + usage)

#### Step 1: Create Railway Account
Visit https://railway.app and sign up with GitHub

#### Step 2: New Project → GitHub Repo
Select your AI Agent repository

#### Step 3: Add Services
Railway auto-detects:
- Python application
- Creates Postgres (optional)

#### Step 4: Configure Environment
```
OPENROUTER_API_KEY=<your_key>
DATABASE_PATH=data/sqlite/conversations.db
LOG_FILE=logs/app.log
```

#### Step 5: Deploy
```bash
git push origin main
# Railway automatically detects changes and deploys
```

**Pros**:
- Seamless GitHub integration
- Better cold-start than Render
- Generous free tier
- Easy database integration

**Cons**:
- Requires careful environment setup
- Limited free tier after credits

---

### Option E: AWS CDK Deployment (Production-Grade)

**Time**: 30-45 minutes  
**Cost**: $20-100/month for production setup  
**Complexity**: High

#### Architecture
```
ALB (Application Load Balancer)
  ↓
ECS Cluster (Fargate)
  ├─ API Service (auto-scaling)
  ├─ Chroma Service
  └─ Monitoring (optional)
  ↓
RDS Aurora PostgreSQL (shared)
ElastiCache Redis (session cache)
S3 (document storage)
CloudWatch (monitoring)
```

#### CDK Code Template
```python
# cdk_stack.py - skeleton provided
from aws_cdk import (
    aws_ecs as ecs,
    aws_rds as rds,
    aws_ec2 as ec2,
    core
)

class AIAgentStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # VPC
        vpc = ec2.Vpc(self, "VPC", max_azs=3)
        
        # RDS Postgres
        db = rds.DatabaseInstance(
            self, "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_13_7
            ),
            vpc=vpc,
            allocated_storage=20
        )
        
        # ECS Cluster
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        
        # Fargate Service
        service = ecs.FargateService(
            self, "Service",
            cluster=cluster,
            task_definition=task_def,
            desired_count=1,
            service_name="ai-agent-api"
        )
        # ... configure auto-scaling, load balancer, etc.
```

**To use this option**:
1. Install AWS CDK: `npm install -g aws-cdk`
2. Configure AWS credentials: `aws configure`
3. Deploy: `cdk deploy`

**Pros**:
- Production-grade infrastructure
- Auto-scaling out of the box
- Managed database
- Enterprise-ready monitoring

**Cons**:
- Complex setup
- AWS cost can increase with usage
- Requires AWS knowledge

---

## Data Persistence Across Deployments

### SQLite (Current - Single Instance)
```
data/sqlite/conversations.db
├─ conversation_sessions
├─ messages
├─ tool_executions
├─ token_usage
└─ system_metrics
```

**Limitations**: 
- Single-machine only
- No concurrent write support

**Migration Path to PostgreSQL**:
```bash
# 1. Update config.py
DATABASE_URL = "postgresql://user:pass@host/ai_agent"

# 2. Same schema works (SQLAlchemy handles dialect differences)
# 3. Run migrations
python -m alembic upgrade head
```

### Chroma Vector Store
```
data/chroma_db/
├─ chroma.sqlite3
└─ documents collection
```

**Persistence**: File-based, survives container restarts  
**Scalability**: Can migrate to Chroma Cloud for production

---

## Environment Variables

### Required
```bash
OPENROUTER_API_KEY=sk-or-v1-...  # LLM API
```

### Optional but Recommended
```bash
DATABASE_PATH=data/sqlite/conversations.db
LOG_FILE=logs/app.log
LOG_LEVEL=INFO
CHROMA_HOST=chroma
CHROMA_PORT=8000
```


---

## Local Testing Checklist

### 1. Start Services
```bash
docker-compose up --build
```

### 2. Test API Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 3. Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "What is your order status?"}'
```

### 4. Test Data Visibility
```bash
# Sessions
curl http://localhost:8000/api/v1/data/sessions

# Analytics
curl http://localhost:8000/api/v1/data/analytics/snapshot

# Token usage
curl http://localhost:8000/api/v1/data/analytics/tokens

# Document versions
curl http://localhost:8000/api/v1/rag/document-versions
```

### 5. Test Chroma
```bash
curl http://localhost:8001/api/v1/heartbeat
```

---

## Production Readiness Checklist

- [ ] Database backed up
- [ ] Environment variables configured
- [ ] HTTPS/TLS enabled (Render/Railway handle this)
- [ ] API rate limiting enabled
- [ ] Monitoring configured
- [ ] Logging aggregation setup
- [ ] Error handling tested
- [ ] Graceful shutdown verified
- [ ] Health checks passing
- [ ] Security audit completed

---

## Troubleshooting

### Container fails to start
```bash
# Check logs
docker-compose logs api

# Check compose validity
docker-compose config

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Chroma connection refused
```bash
# Wait for Chroma to be healthy
docker-compose logs chroma

# Verify Chroma is running
curl http://localhost:8001/api/v1/heartbeat

# Check Docker network
docker network inspect ai_network
```

### Database locked errors
```bash
# SQLite is single-writer; migrate to PostgreSQL for concurrent access
# Temporary fix: increase WAL timeout
sqlite3 data/sqlite/conversations.db "PRAGMA busy_timeout = 5000;"
```

---

## Next Steps

1. **Immediate**: Deploy locally with `docker-compose up`
2. **Short-term**: Try Render.com or Railway.app for live demo
3. **Medium-term**: Enhance observability with cloud-native monitoring (e.g., Datadog, New Relic)
4. **Long-term**: Migrate to AWS CDK for production scale

---

**Status**: Ready for deployment  
**Recommendation**: Start with local Docker, then move to Render/Railway for interviews
