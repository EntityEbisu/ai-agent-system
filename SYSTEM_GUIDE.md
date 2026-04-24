# 🚀 System Guide: Runtime Execution & Observability

**Last Updated**: April 23, 2026  
**System Status**: 🟢 PRODUCTION-READY

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Runtime Execution](#runtime-execution)
- [Observability Dashboard](#observability-dashboard)
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