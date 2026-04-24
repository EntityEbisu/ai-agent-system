# Quick Reference: Enhanced Features

**Last Updated**: April 20, 2026

---

## 🆕 What's New

### 1. Token Tracking ✅
- **What**: Full token count logging (prompt + completion)
- **Where**: Check logs/app.log for `tokens_used` field
- **API**: `GET /api/v1/data/analytics/tokens`
- **Example**:
  ```bash
  curl http://localhost:8000/api/v1/data/analytics/tokens?hours=24
  # → {"total_tokens": 1500, "avg_tokens_per_message": 75, ...}
  ```

### 2. IaC & Microservices ✅
- **What**: Separated services (API, Chroma, Monitoring)
- **How to Use**:
  ```bash
  # Basic (just API + Chroma)
  docker-compose up
  
  # With monitoring (add Grafana, Prometheus, Loki)
  docker-compose --profile monitoring up
  ```
- **Docs**: See `IaC_DOCUMENTATION.md`

### 3. Document Versioning ✅
- **What**: FAQ/policy updates with versioning
- **How to Use**:
  ```bash
  # Check current documents
  curl http://localhost:8000/api/v1/rag/document-versions
  
  # Ingest new/updated document
  curl -X POST "http://localhost:8000/api/v1/rag/ingest?file_path=data/docs/policy.pdf"
  ```
- **Docs**: See `DATA_LIFECYCLE.md`

### 4. Data Visibility ✅
- **What**: Explore sessions, messages, metrics
- **Quick Commands**:
  ```bash
  # Sessions
  curl http://localhost:8000/api/v1/data/sessions
  
  # Session details
  curl http://localhost:8000/api/v1/data/sessions/session-123
  
  # Metrics snapshot
  curl http://localhost:8000/api/v1/data/analytics/snapshot
  
  # Test retrieval
  curl -X POST http://localhost:8000/api/v1/rag/test-retrieval \
    -H "Content-Type: application/json" \
    -d '{"session_id": "test", "message": "What are business risks?"}'
  ```

---

## 📁 New Files

| File | Purpose |
|------|---------|
| `IaC_DOCUMENTATION.md` | Deployment guide (Docker, Render, Railway, AWS) |
| `DATA_LIFECYCLE.md` | Document versioning & update management |
| `app/services/data_introspection.py` | Database & Chroma exploration tools |
| `app/rag/data_lifecycle.py` | Document lifecycle management |
| `observability/*.yml` | Prometheus, Loki configuration |

---

## 🔧 Using the New Features

### Feature 1: Check Token Usage

```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload

# Terminal 2: Make a chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "What is your company policy?"}'

# Terminal 3: Check token report
curl http://localhost:8000/api/v1/data/analytics/tokens?hours=24
```

**Output**:
```json
{
  "message_count": 3,
  "total_tokens": 450,
  "avg_tokens": 150.0,
  "min_tokens": 100,
  "max_tokens": 200
}
```

---

### Feature 2: Test Document Updates

```python
# Python script to test versioning
from app.rag.data_lifecycle import RAGDataLifecycle

lifecycle = RAGDataLifecycle()

# First ingest (creates v1)
result1 = lifecycle.ingest_document(
    "data/docs/Company-10k-18pages.pdf",
    description="Q1 2026 Filing"
)
print(f"Version: {result1['version']}")  # → 1

# Second ingest (detects no change)
result2 = lifecycle.ingest_document(
    "data/docs/Company-10k-18pages.pdf"
)
print(f"Status: {result2['status']}")  # → "unchanged"

# List all versions
versions = lifecycle.list_document_versions()
print(f"Active docs: {lifecycle.get_lifecycle_stats()['active_documents']}")
```

---

### Feature 3: Explore Data via API

```bash
#!/bin/bash
# See all sessions
echo "=== Recent Sessions ==="
curl -s http://localhost:8000/api/v1/data/sessions | jq '.'

# See specific session details
SESSION_ID=$(curl -s http://localhost:8000/api/v1/data/sessions | \
  jq -r '.sessions[0].id')
echo "=== Session $SESSION_ID Messages ==="
curl -s "http://localhost:8000/api/v1/data/sessions/$SESSION_ID" | jq '.'

# See analytics
echo "=== System Metrics ==="
curl -s http://localhost:8000/api/v1/data/analytics/snapshot | jq '.'

# See token usage
echo "=== Token Usage Last 24h ==="
curl -s http://localhost:8000/api/v1/data/analytics/tokens?hours=24 | jq '.'

# See latency
echo "=== Latency Statistics ==="
curl -s http://localhost:8000/api/v1/data/analytics/latency?hours=24 | jq '.'
```

---

### Feature 4: Deploy with Monitoring

```bash
# Start all services including monitoring stack
docker-compose --profile monitoring up --build

# Wait for services to be ready (~30 seconds)
sleep 30

# Access Grafana
open http://localhost:3000
# Login: admin / admin

# Access Prometheus
open http://localhost:9090

# Check Loki
open http://localhost:3100
```

**In Grafana**:
1. Add Prometheus as datasource (http://prometheus:9090)
2. Add Loki as datasource (http://loki:3100)
3. Create dashboard showing:
   - API response times
   - Token usage over time
   - Error rates

---

## 📊 Data Schema

### Token Tracking (in logs)
```json
{
  "event": "response_sent",
  "tokens_used": 150,
  "prompt_tokens": 50,
  "completion_tokens": 100,
  "latency_ms": 45.23,
  "timestamp": "2026-04-20T10:30:00"
}
```

### Document Metadata
```json
{
  "document_id": "Company-10k-18pages",
  "version": 1,
  "content_hash": "sha256_of_content",
  "chunks_count": 111,
  "ingested_at": "2026-04-20T10:00:00",
  "updated_at": "2026-04-20T10:00:00",
  "tags": ["10-k", "filing"]
}
```

---

## 🐛 Troubleshooting

### Tokens Not Recording
- Check: Is `app/main.py` updated? (Should have token counting code)
- Check: Logs should show `tokens_used` in JSON
- Fix: Restart backend: `uvicorn app.main:app --reload`

### Docker Services Won't Start
```bash
# Check what's running
docker-compose ps

# Check logs
docker-compose logs chroma
docker-compose logs api

# Clean up and retry
docker-compose down -v
docker-compose up --build
```

### Chroma Not Responsive
```bash
# Wait longer
sleep 5

# Check health
curl http://localhost:8001/api/v1/heartbeat

# Restart just Chroma
docker-compose restart chroma
```

### Data Visibility Endpoints 404
- Check: API is running: `curl http://localhost:8000/health`
- Check: Correct endpoint: `/api/v1/data/sessions` (not `/data/sessions`)
- Check: Backend logs for errors

---

## 📈 Performance Tips

1. **Query Optimization**:
   - Limit results: `?limit=10`
   - Time range: `?hours=24`
   - Use specific endpoint (faster than general query)

2. **Monitoring**:
   - Don't enable all profiles in production (costs resources)
   - Use `prometheus` profile instead of `monitoring` for high-performance

3. **Storage**:
   - Document versions are stored in `data/chroma_db/document_metadata.json`
   - Archive old docs to save space: `POST /api/v1/rag/archive/{doc_id}`

---

## 🎯 Next Steps

### Immediate (Recommended)
1. ✅ Start backend: `uvicorn app.main:app --reload`
2. ✅ Test token tracking: `curl /api/v1/data/analytics/tokens`
3. ✅ Explore sessions: `curl /api/v1/data/sessions`

### Short-term (1-2 hours)
1. Deploy with `docker-compose --profile monitoring up`
2. Set up Grafana dashboards
3. Test document update workflow

### Medium-term (3-5 hours)
1. Try Render.com deployment (IaC_DOCUMENTATION.md)
2. Set up scheduled document checks
3. Create semantic change detection

### Long-term (Future)
1. Migrate to PostgreSQL (if scaling)
2. Implement change summary generation
3. Add document comparison UI

---

## 📞 Questions?

Refer to:
- `IaC_DOCUMENTATION.md` - Deployment options
- `DATA_LIFECYCLE.md` - Document versioning
- `ASSIGNMENT_ALIGNMENT.md` - Complete feature overview
- `STATUS.md` - Project completion status

---

**Status**: Ready for use  
**Last Tested**: April 20, 2026  
**Production Ready**: Yes
