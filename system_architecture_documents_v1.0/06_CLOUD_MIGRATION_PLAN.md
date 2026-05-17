# 06_CLOUD_MIGRATION_PLAN.md

**AWS Production Migration – Interview‑Ready Plan**

*All statements are based only on the audited artifacts (`00_ARCHITECTURE_MAP.md`, `01_IMPLEMENTATION_AUDIT.md`, `03_LANDMINES.md`). No assumptions beyond the existing code are made.*

---

## 1. Current State (On‑Prem / Local)
| Component | Implementation | Evidence |
|-----------|----------------|----------|
| API Layer | FastAPI app (`app/main.py`) | `01_IMPLEMENTATION_AUDIT.md` – API entrypoint implemented |
| Routing / Workflow | `app/agent/router.py` & `app/agent/workflow.py` (mock tool) | Audit lines 13‑24 |
| RAG Pipeline | `app.rag.pipeline` using Chroma DB + LLM | Audit lines 31‑35 |
| Session Memory | In‑process dict (`app.agent.memory`) | Audit lines 25‑29 |
| Persistence | SQLite via SQLAlchemy (`app/data/models.py`) | Audit lines 49‑53 |
| Vector Store | Chroma DB (in‑memory/SQLite) | Audit lines 43‑47 |
| Observability | Prometheus metrics, basic logging, Loki config **not wired** | Audit lines 55‑60 |
| Deployment | Dockerfile & `docker‑compose.yml` present but never invoked | Audit lines 67‑75 |

## 2. Production Target Architecture on AWS
```
API Gateway → AWS Lambda (or ECS Fargate) → FastAPI container
   │                                 │
   │                                 ├─ Redis (session store)
   │                                 ├─ Amazon RDS (PostgreSQL) – persistence
   │                                 ├─ Amazon S3 (static assets, vector DB backups)
   │                                 └─ Managed Vector DB (Amazon OpenSearch with k‑NN or Pinecone)
   │
   └─ CloudWatch (metrics & logs) → Loki (optional via Grafana Cloud)
```

### Service Mapping
| AWS Service | Role | Why use it | Problem it solves | Migration complexity | Trade‑offs |
|------------|------|------------|-------------------|----------------------|-----------|
| **API Gateway** | Public entry point, request throttling, auth integration | Provides a managed, secure front‑door; can enforce JWT validation | Replaces direct exposure of FastAPI on the internet | Low – just point to Lambda/ECS endpoint | Adds an extra hop, slight latency increase |
| **AWS Lambda** (or **ECS Fargate**) | Host FastAPI app | Serverless scaling (Lambda) or container‑level control (ECS) | Eliminates managing EC2 instances; auto‑scales with traffic | Medium – package app as a container image, adjust entrypoint | Lambda cold‑start latency; ECS cost at low traffic |
| **Amazon RDS (PostgreSQL)** | Persistent relational storage | ACID guarantees, connection pooling, backups | Replaces SQLite which cannot handle concurrent writes | Medium – migrate schema with Alembic, data dump from SQLite | Higher cost, requires VPC configuration |
| **Amazon ElastiCache (Redis)** | Session store | Durable, fast key‑value store, survives container restarts | Solves in‑memory session loss (Landmine #4) | Low – replace `app.agent.memory` with Redis client calls | Adds operational overhead, need TTL management |
| **Amazon S3** | Object storage for large files, vector DB snapshots | Cheap, durable storage for embeddings, model artefacts | Provides backup for Chroma DB files, future bulk import | Low – upload/download via boto3 | Eventual consistency for reads |
| **Managed Vector DB** (OpenSearch k‑NN or Pinecone) | Vector similarity search | Scalable, persisted embeddings, high‑dimensional indexing | Overcomes Chroma durability limits (Landmine #9) | Medium – export current embeddings, re‑index in new store | Vendor lock‑in, cost per query |
| **CloudWatch** | Metrics & log aggregation | Native AWS monitoring, alarms, dashboards | Replaces ad‑hoc Prometheus scraping; integrates with Loki if desired | Low – emit standard CloudWatch metrics from code | Limited custom visualisation compared to Grafana |
| **AWS Secrets Manager** | Secure storage of API keys, DB credentials | Centralised secret rotation, IAM‑based access | Removes hard‑coded secrets from codebase | Low – replace env vars with Secrets Manager calls | Slight latency for secret retrieval |
| **IAM Roles** | Permission boundaries for each service | Least‑privilege security model | Prevents over‑privileged containers/Lambda functions | Low – attach policies to task roles | Requires careful policy design |

## 3. Migration Path (Phased)
1. **Containerise the Application** – Build a Docker image (already exists) and push to Amazon ECR.
2. **Introduce Managed Persistence** –
   - Export SQLite data (`sqlite3 db.sqlite .dump`).
   - Create PostgreSQL schema via Alembic migrations.
   - Import data into RDS.
   - Update `app/data/models.py` to point to the RDS URL (use Secrets Manager for credentials).
3. **Externalise Session State** – Replace the in‑process dict with a Redis client (`redis-py`).
   - Add a thin abstraction layer so the same API works locally and in AWS.
4. **Swap Vector Store** –
   - Export current Chroma embeddings to JSON.
   - Bulk‑load into the chosen managed vector DB.
   - Update `app.rag.retriever` to use the new client SDK.
5. **Deploy to AWS** –
   - Create an API Gateway → Lambda (or ECS) integration.
   - Configure Lambda memory/timeout for LLM calls.
   - Attach IAM role with permissions for RDS, Redis, S3, and Secrets Manager.
6. **Observability Upgrade** –
   - Replace Prometheus metrics with CloudWatch custom metrics (`boto3` client).
   - Wire Loki exporter if Grafana Cloud is used; otherwise rely on CloudWatch Logs.
7. **Security Harden** –
   - Enable JWT validation at API Gateway.
   - Add rate‑limiting via API Gateway usage plans.
   - Implement input validation in FastAPI models.
8. **CI/CD Enablement** –
   - Add GitHub Actions to build Docker image, run tests, and push to ECR.
   - Deploy via AWS CDK or CloudFormation stacks.

## 4. Risk & Mitigation Summary
| Risk | Impact | Mitigation |
|------|--------|------------|
| Data migration errors | Service downtime | Perform dry‑run migrations in a staging VPC, use backups in S3 |
| Cold start latency (Lambda) | Slower first request | Keep a warm pool or use provisioned concurrency; alternatively use ECS Fargate |
| Secrets leakage | Security breach | Enforce IAM policies, rotate secrets regularly via Secrets Manager |
| Vendor lock‑in to managed vector DB | Future migration cost | Abstract retriever behind an interface; keep export scripts ready |

---

**Result:** The plan translates the current demo architecture into a production‑grade, AWS‑native stack while directly addressing the landmines identified in `03_LANDMINES.md`.
