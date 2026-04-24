# 🧪 Complete Testing & Verification Guide

**Last Updated**: April 20, 2026  
**Project Status**: ✅ Level 100/200/300 - ALL TESTS PASSING

---

## Quick Start

### Run All Tests at Once (Recommended)

```bash
cd /home/tminh/ai-agent-system

# Terminal 1: Start the API backend
uvicorn app.main:app --reload

# Terminal 2: Run comprehensive test suite (in another terminal)
python scripts/comprehensive_test.py

# Terminal 3: Run frontend integration tests (in another terminal)
python scripts/test_frontend_integration.py
```

**Expected Output**: ✅ 7/7 comprehensive tests pass + ✅ 8/8 frontend integration tests pass

---

## Test Suite Overview

Your project now has **two comprehensive test suites**:

### 1. **Comprehensive Test Suite** (`scripts/comprehensive_test.py`)
Tests Level 100/200/300 core components:
- ✅ Imports (FastAPI, LangChain, Chroma, SQLAlchemy, Pydantic, Streamlit)
- ✅ RAG Pipeline (document retrieval, embeddings, vector store)
- ✅ Order Status Workflow (multi-turn state machine)
- ✅ Session Memory (in-memory state persistence)
- ✅ SQLite Database (table creation, data persistence)
- ✅ Logging & Metrics (JSON output, metric collection)
- ✅ FastAPI Endpoints (/health, /metrics, /chat)

**Run**: `python scripts/comprehensive_test.py`  
**Expected**: 7/7 tests pass in ~25-30 seconds

---

### 2. **Frontend Integration Test Suite** (`scripts/test_frontend_integration.py`)
Tests the entire frontend-to-backend integration:
- ✅ Frontend Dependencies (Streamlit, Requests, JSON)
- ✅ Database Persistence (SQLite operations)
- ✅ Logging & Observability (JSON logger, metrics)
- ✅ API Health Endpoint (/health)
- ✅ API Metrics Endpoint (/metrics)
- ✅ Chat Streaming (/chat with NDJSON responses)
- ✅ Order Workflow Integration (full 4-step flow)
- ✅ RAG Query Integration (document Q&A)

**Run**: `python scripts/test_frontend_integration.py`  
**Expected**: 8/8 tests pass in ~30-40 seconds

---

## Complete Testing Flow (Step-by-Step)

### Step 1: Initialize the Database

```bash
python scripts/setup_db.py
```

**Expected Output**:
```
✅ Database initialized successfully!
Created tables:
  ✓ conversation_sessions
  ✓ messages
  ✓ tool_executions
  ✓ token_usage
  ✓ system_metrics
```

---

### Step 2: Start the API Backend

**Terminal 1**:
```bash
# Optional: Set environment variables
export LOG_FILE=logs/app.log
export LOG_LEVEL=INFO

# Start backend
uvicorn app.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Verify it's working**:
```bash
curl http://localhost:8000/health | jq .
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Step 3: Run Core System Tests

**Terminal 2**:
```bash
python scripts/comprehensive_test.py
```

**Full Output Example**:
```
============================================================
                  COMPREHENSIVE TEST SUITE                  
            Level 100/200/300 System Validation             
============================================================

===== Testing Imports =====
✅ FastAPI
   → ✓ Available
✅ LangChain Core
   → ✓ Available
✅ Chroma
   → ✓ Available
✅ SQLAlchemy
   → ✓ Available
✅ Pydantic
   → ✓ Available
✅ Streamlit
   → ✓ Available

===== Level 100: RAG Pipeline =====
✅ Retriever Initialization
   → Chroma loaded
✅ Retrieval (4 docs)
   → Retrieved 4 chunks for 'seasonality revenue'
   → Sample: technology. We have licensed in the past...

===== Level 100: Order Status Workflow =====
✅ Workflow Initialization
   → State machine started
✅ Step 1: Name Collection
   → Received: 'Please provide the last 4 digits of your SSN.'
✅ Step 2: SSN Collection
   → Received: 'Please provide your date of birth (YYYY-MM-DD).'
✅ Step 3: DOB & Tool Execution
   → Received: 'Your order has been shipped and will arrive in 2 d'
✅ State Reset After Execution
   → Tool state cleared

===== Level 100: Session Memory =====
✅ Session Creation
   → Session ID: test-session-123
✅ Data Persistence
   → Values retained across calls

===== Level 300: SQLite Persistence =====
✅ Database Connection
   → SQLite @ conversations.db
✅ Table Creation (5 tables)
   → All required tables present: conversation_sessions, messages, system_metrics, token_usage, tool_executions
✅ Data Storage & Retrieval
   → Session persisted to database

===== Level 300: Observability & Logging =====
✅ Logger Initialization
   → JSON logger ready
✅ Request Logging
   → Event captured
✅ Metrics Collection
   → Collected 4 metric groups
✅ Timer Context Manager
   → Measured 10.1ms

===== Level 200: FastAPI Endpoints =====
✅ GET /health
   → Status: 200
✅ GET /metrics
   → Status: 200
✅ POST /chat
   → Status: 200

===== Test Summary =====
✅ Imports
✅ RAG Pipeline (L100)
✅ Order Workflow (L100)
✅ Session Memory (L100)
✅ Database (L300)
✅ Observability (L300)
✅ FastAPI Endpoints (L200)

Result: 7/7 tests passed
Time: 27.27s

🎉 ALL TESTS PASSED!
```

---

### Step 4: Run Frontend Integration Tests

**Terminal 3**:
```bash
python scripts/test_frontend_integration.py
```

**Full Output Example**:
```
╔====================================================================╗
║                  FRONTEND INTEGRATION TEST SUITE                   ║
║               Level 100/200/300 Frontend Validation                ║
╚====════════════════════════════════════════════════════════════════╝

⏳ Checking if API server is running...
✅ API server is running

======================================================================
                     Frontend: Import Validation                      
======================================================================

✅ Import streamlit
   → Available
✅ Import requests
   → Available
✅ Import json
   → Available

======================================================================
                     Database: SQLite Persistence                     
======================================================================

✅ Database File
   → SQLite @ conversations.db
✅ Tables (5)
   → Tables: conversation_sessions, messages, system_metrics, token_usage, tool_executions
✅ Data Storage
   → Session persisted

======================================================================
                   Observability: Logging & Metrics                   
======================================================================

✅ Logger Initialization
   → JSON logger ready
✅ Metrics Collection
   → Collected metrics: ['latency_/chat', 'tokens_used', 'cost_usd']
✅ Timer Measurement
   → Measured 10.2ms

======================================================================
                      Backend API: Health Check                       
======================================================================

✅ GET /health
   → Status: 200
✅ Response Format
   → Response: {"status": "healthy", "version": "1.0.0"}

======================================================================
                    Backend API: Metrics Endpoint                     
======================================================================

✅ GET /metrics
   → Status: 200
✅ Response Format
   → Response is dict (not list): dict

======================================================================
                Backend API: Chat Endpoint (Streaming)                
======================================================================

✅ POST /chat
   → Status: 200
✅ Streaming Format
   → Received 1 tokens
✅ Response Content
   → Response: 'To check your order status, please provide your full name.'
✅ JSON Parsing
   → Parsed 1 valid JSON lines

======================================================================
               Backend API: Order Workflow (Full Flow)                
======================================================================

✅ Step 1: Where is my order?
   → Response includes 'name'
✅ Step 2: Alice Nguyen
   → Response includes 'SSN'
✅ Step 3: 1234
   → Response includes 'YYYY-MM-DD'
✅ Step 4: 1990-01-01
   → Response includes 'shipped'

======================================================================
             Backend API: RAG Query (Document Retrieval)              
======================================================================

✅ RAG Query
   → Status: 200
✅ Response Content
   → Response length: 1044 chars
✅ Response Preview
   → 'The document mentions two primary business risks...'

======================================================================
                             Test Summary                             
======================================================================

✅ PASS: Frontend Imports
✅ PASS: Database
✅ PASS: Logging & Metrics
✅ PASS: API Health
✅ PASS: API Metrics
✅ PASS: Chat Endpoint
✅ PASS: Order Workflow
✅ PASS: RAG Query

Result: 8/8 test categories passed

🎉 ALL TESTS PASSED!
```

---

### Step 5: Launch the Streamlit Web UI (Optional)

**Terminal 4**:
```bash
streamlit run frontend/streamlit_app.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://YOUR_IP:8501
```

**In Browser** (http://localhost:8501):
1. ✅ Health indicator shows 🟢 API Online
2. ✅ Session ID displayed in sidebar
3. ✅ Chat interface functional
4. ✅ Can ask "Where is my order?" → workflows through 4 steps
5. ✅ Can ask RAG questions like "What are business risks?"
6. ✅ Conversation history persists in UI
7. ✅ Metrics display in sidebar

---

## Individual Component Testing

### Test RAG Pipeline

```bash
# Minimal test - verify Chroma loads and retrieves documents
python scripts/validate_project.py
```

**Expected**:
- ✅ Chroma loads successfully
- ✅ Retrieves 2+ document chunks
- ✅ Chunks contain relevant content

---

### Test Order Workflow Directly

```python
# Python script to test workflow
from app.agent.workflow import start_tool_flow, handle_tool_flow

state = {"tool_state": None}

# Start workflow
response1 = start_tool_flow(state)
print(f"Step 1: {response1}")
# Expected: "To check your order status, please provide your full name."

# Collect name
response2 = handle_tool_flow("John Doe", state)
print(f"Step 2: {response2}")
# Expected: "Please provide the last 4 digits of your SSN."

# Collect SSN
response3 = handle_tool_flow("1234", state)
print(f"Step 3: {response3}")
# Expected: "Please provide your date of birth (YYYY-MM-DD)."

# Collect DOB
response4 = handle_tool_flow("1990-01-01", state)
print(f"Step 4: {response4}")
# Expected: "Your order has been shipped and will arrive in X days."
```

---

### Test API Endpoints Manually

#### Health Check
```bash
curl http://localhost:8000/health | jq .
```

**Expected**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

#### Metrics
```bash
curl http://localhost:8000/metrics | jq .
```

**Expected** (empty initially, grows as you use the system):
```json
{}
```

**After making chat requests**, will show:
```json
{
  "latency_/chat": {
    "count": 5,
    "avg": 2345.2,
    "min": 1200.5,
    "max": 4500.0
  },
  "tokens_used": {
    "count": 5,
    "avg": 125.4,
    "min": 50,
    "max": 250
  },
  "cost_usd": {
    "count": 5,
    "avg": 0.00125,
    "min": 0.0005,
    "max": 0.0025
  }
}
```

---

#### Chat with Streaming

```bash
# Send a message to the order workflow
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-1","message":"Where is my order?"}'
```

**Expected** (NDJSON format - newline delimited JSON):
```
{"token":"To"}
{"token":" "}
{"token":"check"}
{"token":" "}
{"token":"your"}
{"token":" "}
{"token":"order"}
{"token":" "}
{"token":"status"}
{"token":","}
{"token":" "}
{"token":"please"}
{"token":" "}
{"token":"provide"}
{"token":" "}
{"token":"your"}
{"token":" "}
{"token":"full"}
{"token":" "}
{"token":"name"}
{"token":"."}
```

---

### Test Database Operations

```bash
# Query conversations from database
python << 'EOF'
from app.data.models import init_db, ConversationSession

db_url = "sqlite:///data/sqlite/conversations.db"
Session, _ = init_db(db_url)
session = Session()

# Get all conversations
convs = session.query(ConversationSession).all()
print(f"Total conversations: {len(convs)}")

for conv in convs[:5]:
    print(f"  - ID: {conv.id}")
    print(f"    User: {conv.user_id}")
    print(f"    Type: {conv.context_type}")
    print(f"    Created: {conv.created_at}")

session.close()
EOF
```

**Expected**:
```
Total conversations: 12
  - ID: test-session-20260420-123456
    User: user-001
    Type: order_status
    Created: 2026-04-20 10:30:45.123456
  ... more entries ...
```

---

### Test Logging Output

```bash
# Check JSON logs written to file
cat logs/app.log | jq . | head -20
```

**Expected Format** (JSON):
```json
{
  "timestamp": "2026-04-20T10:30:45.123456",
  "level": "INFO",
  "name": "ai-agent-system",
  "message": "{\"event\": \"request_received\", \"endpoint\": \"/chat\", \"method\": \"POST\", \"session_id\": \"test-1\", \"message_preview\": \"Where is my order?\", \"timestamp\": \"2026-04-20T10:30:45.123456\"}"
}
```

---

## Docker Testing (Level 200)

### Build and Run with Docker

```bash
# Build image
docker build -t ai-agent-system:latest .

# Run with docker-compose
docker-compose up --build
```

**Expected**:
```
backend_1 | INFO:     Uvicorn running on http://0.0.0.0:8000
backend_1 | INFO:     Application startup complete
```

**Test endpoints**:
```bash
# Wait 5 seconds for container to be ready
sleep 5

# Health check
curl http://localhost:8000/health | jq .

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"docker-test","message":"What are business risks?"}'
```

---

## Performance & Metrics

### Verify Metrics Collection

After running tests, check `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics | jq '.latency_/chat'
```

**Expected**:
- `count`: Number of requests
- `avg`: Average latency in milliseconds
- `min`: Minimum latency
- `max`: Maximum latency

### Example Performance Metrics

```json
{
  "latency_/chat": {
    "count": 15,
    "avg": 2156.34,
    "min": 987.23,
    "max": 4532.12
  }
}
```

---

## Troubleshooting

### Issue: "API server not running"

**Solution**:
```bash
# Start backend in a separate terminal
uvicorn app.main:app --reload

# Verify it's running
curl http://localhost:8000/health
```

---

### Issue: "Database file not found"

**Solution**:
```bash
# Initialize database
python scripts/setup_db.py
```

---

### Issue: "Streamlit can't connect to API"

**Solution**:
1. Ensure backend is running: `uvicorn app.main:app --reload`
2. Check firewall isn't blocking port 8000
3. Ensure API is accessible: `curl http://localhost:8000/health`

---

### Issue: "Chroma deprecation warning"

**Note**: This is a LangChain deprecation warning that doesn't affect functionality. It's safe to ignore for now. To remove it, run:
```bash
pip install langchain-chroma
```

---

### Issue: "Tests fail with 'module not found' errors"

**Solution**:
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Verify specific packages
pip list | grep -i langchain
pip list | grep -i sqlalchemy
pip list | grep -i streamlit
```

---

## Test Summary Table

| **Component** | **Test Script** | **Command** | **Expected** | **Status** |
|---|---|---|---|---|
| **Imports** | comprehensive_test.py | `python scripts/comprehensive_test.py` | 6 libraries load | ✅ PASS |
| **RAG Pipeline** | comprehensive_test.py | (included above) | 4 chunks retrieved | ✅ PASS |
| **Order Workflow** | comprehensive_test.py | (included above) | 4-step flow complete | ✅ PASS |
| **Session Memory** | comprehensive_test.py | (included above) | State persists | ✅ PASS |
| **Database** | comprehensive_test.py | (included above) | 5 tables created | ✅ PASS |
| **Logging** | comprehensive_test.py | (included above) | JSON output | ✅ PASS |
| **FastAPI** | comprehensive_test.py | (included above) | /health, /metrics, /chat work | ✅ PASS |
| **Frontend** | test_frontend_integration.py | `python scripts/test_frontend_integration.py` | All components work | ✅ PASS |
| **Streamlit UI** | Manual | `streamlit run frontend/streamlit_app.py` | UI at localhost:8501 | ✅ PASS |
| **Docker** | Manual | `docker-compose up --build` | Server on port 8000 | ✅ READY |

---

## End-to-End Demo Flow (10 minutes)

```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload

# Terminal 2: Run tests
python scripts/comprehensive_test.py && python scripts/test_frontend_integration.py

# Terminal 3: Start UI (optional)
streamlit run frontend/streamlit_app.py

# Browser: http://localhost:8501
# Test order workflow: "Where is my order?" → Alice Nguyen → 1234 → 1990-01-01
# Test RAG: "What are the business risks?"
```

---

## Next Steps

✅ **All tests passing?**
- ✅ Core functionality verified
- ✅ Frontend integration confirmed
- ✅ Database persistence working
- ✅ API endpoints operational
- ✅ Logging & metrics functional

**Ready to**:
1. Deploy to cloud (Render/Railway) - 3-5 hours
2. Add Prometheus/Grafana monitoring - 2-3 hours
3. Implement RAG evaluation pipeline - 3-5 hours
4. Migrate to PostgreSQL - 2-3 hours

---

**Project Status**: 🟢 **FULLY TESTED & PRODUCTION-READY**

All Level 100, 200, and 300 components verified and working.
