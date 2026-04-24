# 🚀 System Guide: Runtime Execution & Observability

**Last Updated**: April 23, 2026  
**System Status**: 🟢 PRODUCTION-READY

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Runtime Execution](#runtime-execution)
- [Observability Dashboard](#observability-dashboard)
- [Troubleshooting](#troubleshooting)
- [Performance Monitoring](#performance-monitoring)
- [Maintenance Procedures](#maintenance-procedures)

---

## Quick Start

### Start the Complete System

```bash
# Terminal 1: Backend API
cd /home/tminh/ai-agent-system
uvicorn app.main:app --reload

# Terminal 2: Frontend UI
streamlit run frontend/streamlit_app.py

# Terminal 3: Run Tests (optional verification)
python tests/run_all_tests.py
```

**Expected Result**:
- API: http://localhost:8000 (FastAPI docs at /docs)
- UI: http://localhost:8501 (Streamlit chat interface)
- Tests: 15/15 passing

---

## Runtime Execution

### 🏃‍♂️ Starting the System

#### Option 1: Development Mode (Recommended)

```bash
# Backend API with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal: Frontend
streamlit run frontend/streamlit_app.py --server.port 8501
```

#### Option 2: Docker Compose (Production)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d
```

#### Option 3: Manual Python Execution

```bash
# Set environment variables
export LOG_LEVEL=INFO
export LOG_FILE=logs/app.log

# Run backend
python -m app.main

# Frontend (another terminal)
streamlit run frontend/streamlit_app.py
```

### 🔧 Environment Configuration

Create `.env` file in project root:

```bash
# Required
OPENROUTER_API_KEY=your_api_key_here
LLM_PROVIDER=openrouter
EMBEDDING_PROVIDER=huggingface

# Optional
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
DATABASE_URL=sqlite:///data/sqlite/conversations.db
```

### 📊 System Resources

**Minimum Requirements**:
- Python 3.9+
- 4GB RAM
- 2GB Disk space
- Internet connection (for LLM API calls)

**Recommended**:
- Python 3.11+
- 8GB RAM
- 10GB Disk space
- Stable internet connection

---

## Observability Dashboard

### 🎛️ Built-in Dashboards

#### 1. FastAPI Interactive Docs
**URL**: http://localhost:8000/docs
**Features**:
- Interactive API testing
- Request/response schemas
- Real-time endpoint testing
- Authentication (if configured)

#### 2. Streamlit Frontend Dashboard
**URL**: http://localhost:8501
**Features**:
- Real-time chat interface
- Session history viewer
- RAG document explorer
- System metrics display
- Log file viewer

#### 3. Health & Metrics Endpoints

**Health Check**:
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "1.0.0"}
```

**Metrics Endpoint**:
```bash
curl http://localhost:8000/metrics
# Response: JSON object with performance metrics
```

### 📈 Monitoring Components

#### Application Logs
**Location**: `logs/app.log`
**Format**: JSON structured logging
**Sample Entry**:
```json
{
  "timestamp": "2026-04-23T03:08:56.487766",
  "level": "INFO",
  "name": "ai-agent-system",
  "message": {
    "event": "request_received",
    "endpoint": "/chat",
    "method": "POST",
    "session_id": "test-session",
    "message_preview": "test message",
    "timestamp": "2026-04-23T03:08:56.487766"
  }
}
```

#### Database Monitoring
**Location**: `data/sqlite/conversations.db`
**Tools**:
```bash
# View recent conversations
sqlite3 data/sqlite/conversations.db "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;"

# Count total messages
sqlite3 data/sqlite/conversations.db "SELECT COUNT(*) FROM messages;"
```

#### Vector Store Monitoring
**Location**: `data/chroma_db/`
**Status Check**:
```python
from app.rag.retriever import get_retriever
retriever = get_retriever()
docs = retriever.get_relevant_documents("test query")
print(f"Retrieved {len(docs)} documents")
```

### 📊 Key Metrics to Monitor

| Metric | Location | Normal Range | Alert Threshold |
|--------|----------|--------------|-----------------|
| API Response Time | `/metrics` | <2 seconds | >5 seconds |
| Chat Streaming Latency | Logs | <3 seconds | >10 seconds |
| Database Connections | SQLite logs | N/A | Connection errors |
| RAG Retrieval Count | Logs | 3-5 docs | 0 docs |
| Memory Usage | System monitor | <2GB | >4GB |

---

## Troubleshooting

### 🔍 Common Issues & Solutions

#### Issue 1: API Server Won't Start
**Symptoms**: `ModuleNotFoundError`, `ImportError`, port already in use
**Solutions**:
```bash
# Check Python environment
python --version
pip list | grep fastapi

# Install dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8000
kill -9 <PID>

# Try different port
uvicorn app.main:app --reload --port 8001
```

#### Issue 2: LLM API Errors
**Symptoms**: `AuthenticationError`, `RateLimitError`, timeout errors
**Solutions**:
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Switch providers in .env
LLM_PROVIDER=gemini  # if you have GEMINI_API_KEY
```

#### Issue 3: RAG Retrieval Fails
**Symptoms**: No documents returned, empty responses
**Solutions**:
```bash
# Check vector store
ls -la data/chroma_db/

# Re-ingest documents
python -c "from app.rag.ingest import ingest_documents; ingest_documents()"

# Test retriever
python -c "from app.rag.retriever import get_retriever; r = get_retriever(); print(r.get_relevant_documents('test'))"
```

#### Issue 4: Database Connection Errors
**Symptoms**: `OperationalError`, data not persisting
**Solutions**:
```bash
# Initialize database
python tests/setup_db.py

# Check database file
ls -la data/sqlite/conversations.db

# Verify tables
sqlite3 data/sqlite/conversations.db ".tables"
```

#### Issue 5: Frontend Connection Issues
**Symptoms**: Streamlit can't connect to API
**Solutions**:
```bash
# Check API is running
curl http://localhost:8000/health

# Check CORS settings (if needed)
# Add to app/main.py:
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

#### Issue 6: High Memory Usage
**Symptoms**: System slowdown, out of memory errors
**Solutions**:
```bash
# Monitor memory
top -p $(pgrep -f uvicorn)

# Restart services
docker-compose restart

# Clear caches (if applicable)
rm -rf data/chroma_db/
python -c "from app.rag.ingest import ingest_documents; ingest_documents()"
```

#### Issue 7: Streaming Responses Not Working
**Symptoms**: Chat responses come all at once instead of streaming
**Solutions**:
```bash
# Check client supports streaming
# Frontend should use:
response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    # process NDJSON

# Test API directly
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'
```

### 🐛 Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
export PYTHONPATH=/home/tminh/ai-agent-system
uvicorn app.main:app --reload --log-level debug
```

### 📞 Getting Help

1. **Check Logs**: `tail -f logs/app.log`
2. **Run Tests**: `python tests/run_all_tests.py`
3. **Validate Components**: `python tests/validate_project.py`
4. **Check Documentation**: See [TESTING_AND_VERIFICATION.md](TESTING_AND_VERIFICATION.md)

---

## Performance Monitoring

### ⚡ Performance Benchmarks

**API Endpoints**:
- `/health`: <100ms
- `/metrics`: <200ms
- `/chat`: 2-5 seconds (includes LLM call)

**RAG Pipeline**:
- Document ingestion: 30-60 seconds (first run)
- Retrieval: 200-500ms
- Generation: 1-3 seconds

**Database Operations**:
- Message persistence: <50ms
- Session queries: <100ms

### 📈 Scaling Considerations

#### Vertical Scaling (Single Instance)
- **CPU**: More cores help with concurrent requests
- **RAM**: 8GB+ recommended for multiple users
- **Disk**: SSD recommended for vector store I/O

#### Horizontal Scaling (Multiple Instances)
- **Session Affinity**: Required for conversation memory
- **Shared Database**: SQLite not suitable, migrate to PostgreSQL
- **Load Balancer**: Nginx or AWS ALB for distribution

#### Caching Strategies
- **Vector Store**: Keep in memory for faster retrieval
- **API Responses**: Cache frequent queries
- **Embeddings**: Pre-compute for static documents

---

## Maintenance Procedures

### 🛠️ Regular Maintenance

#### Daily
```bash
# Check system health
curl http://localhost:8000/health

# Monitor logs for errors
grep ERROR logs/app.log

# Check disk usage
df -h data/
```

#### Weekly
```bash
# Run full test suite
python tests/run_all_tests.py

# Clean old logs (keep last 7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Database maintenance
sqlite3 data/sqlite/conversations.db "VACUUM;"
```

#### Monthly
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Re-ingest documents (if updated)
python -c "from app.rag.ingest import ingest_documents; ingest_documents()"

# Archive old data
# Move old conversations to archive/
```

### 🔄 Backup Procedures

#### Database Backup
```bash
# Create backup
cp data/sqlite/conversations.db data/sqlite/conversations.db.backup

# Automated backup script
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp data/sqlite/conversations.db $BACKUP_DIR/
cp -r data/chroma_db $BACKUP_DIR/
```

#### Configuration Backup
```bash
# Backup configs
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

### 🚨 Emergency Procedures

#### System Down
1. Check logs: `tail -f logs/app.log`
2. Restart services: `docker-compose restart`
3. If persistent, check system resources: `top`, `df -h`
4. Restore from backup if needed

#### Data Loss
1. Stop all services
2. Restore from backup: `cp backups/latest/conversations.db data/sqlite/`
3. Restart services
4. Validate with tests: `python tests/run_all_tests.py`

#### Security Incident
1. Rotate API keys in `.env`
2. Check logs for suspicious activity
3. Update dependencies: `pip install --upgrade -r requirements.txt`
4. Restart all services

---

## 📞 Support & Resources

### Documentation Links
- [Testing Guide](TESTING_AND_VERIFICATION.md) - Complete testing procedures
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Changelog](CHANGELOG.md) - Version history and updates
- [Architecture](PROJECT_FLOW.md) - System design details

### Key Files for Troubleshooting
- `logs/app.log` - Application logs
- `data/sqlite/conversations.db` - Database file
- `data/chroma_db/` - Vector store
- `.env` - Configuration
- `docker-compose.yml` - Service configuration

### Getting Help
1. Check this guide first
2. Run the test suite: `python tests/run_all_tests.py`
3. Review logs and metrics
4. Check GitHub issues for known problems
5. Contact development team with specific error messages