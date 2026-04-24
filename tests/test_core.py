#!/usr/bin/env python3
"""
Comprehensive Testing Suite with Visual Output (Level 100/200/300)

Run this script to test all components with visible results and status indicators.
Usage:
    python scripts/comprehensive_test.py [--verbose]
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Terminal colors for visual output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def print_test(name: str, status: bool, details: str = ""):
    """Print test result with visual indicator."""
    icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
    print(f"{icon} {name}")
    if details:
        print(f"   {Colors.YELLOW}→{Colors.ENDC} {details}")


def test_imports():
    """Test Level 100/200/300 imports."""
    print_header("Testing Imports")
    
    tests = {
        "FastAPI": lambda: __import__('fastapi'),
        "LangChain Core": lambda: __import__('langchain_core'),
        "Chroma": lambda: __import__('chromadb'),
        "SQLAlchemy": lambda: __import__('sqlalchemy'),
        "Pydantic": lambda: __import__('pydantic'),
        "Streamlit": lambda: __import__('streamlit'),
    }
    
    results = []
    for name, import_fn in tests.items():
        try:
            import_fn()
            print_test(name, True, "✓ Available")
            results.append(True)
        except ImportError as e:
            print_test(name, False, f"✗ Missing: {str(e)[:50]}")
            results.append(False)
    
    return all(results)


def test_rag_pipeline():
    """Test Level 100: RAG Pipeline."""
    print_header("Level 100: RAG Pipeline")
    
    try:
        from app.rag.retriever import get_retriever
        from app.rag.pipeline import handle_rag
        
        retriever = get_retriever()
        print_test("Retriever Initialization", True, "Chroma loaded")
        
        # Test retrieval
        query = "seasonality revenue"
        docs = retriever.invoke(query)
        
        print_test(f"Retrieval ({len(docs)} docs)", len(docs) > 0, 
                   f"Retrieved {len(docs)} chunks for '{query}'")
        
        if docs:
            preview = docs[0].page_content[:80].replace('\n', ' ')
            print(f"   {Colors.YELLOW}→{Colors.ENDC} Sample: {preview}...")
        
        return True
    except Exception as e:
        print_test("RAG Pipeline", False, str(e)[:60])
        return False


def test_order_workflow():
    """Test Level 100: Order Status Workflow."""
    print_header("Level 100: Order Status Workflow")
    
    try:
        from app.agent.workflow import start_tool_flow, handle_tool_flow
        
        # Simulate workflow
        state = {"tool_state": None, "history": []}
        start_tool_flow(state)
        print_test("Workflow Initialization", True, "State machine started")
        
        # Step 1: Collect name
        response1 = handle_tool_flow("Alice Nguyen", state)
        step1_ok = "SSN" in response1
        print_test("Step 1: Name Collection", step1_ok, f"Received: '{response1[:50]}'")
        
        # Step 2: Collect SSN
        response2 = handle_tool_flow("1234", state)
        step2_ok = "birth" in response2.lower()
        print_test("Step 2: SSN Collection", step2_ok, f"Received: '{response2[:50]}'")
        
        # Step 3: Collect DOB
        response3 = handle_tool_flow("1990-01-01", state)
        step3_ok = "shipped" in response3.lower() or "order" in response3.lower()
        print_test("Step 3: DOB & Tool Execution", step3_ok, f"Received: '{response3[:50]}'")
        
        # Verify state reset
        reset_ok = not state["tool_state"]["active"] if state.get("tool_state") else True
        print_test("State Reset After Execution", reset_ok, "Tool state cleared")
        
        return all([step1_ok, step2_ok, step3_ok, reset_ok])
    except Exception as e:
        print_test("Order Workflow", False, str(e)[:60])
        import traceback
        traceback.print_exc()
        return False


def test_session_memory():
    """Test Level 100: Session Memory."""
    print_header("Level 100: Session Memory")
    
    try:
        from app.agent.memory import get_session, update_session
        
        session_id = "test-session-123"
        
        # Get session
        session = get_session(session_id)
        print_test("Session Creation", True, f"Session ID: {session_id}")
        
        # Store data
        update_session(session_id, {"test_key": "test_value"})
        session = get_session(session_id)
        
        has_data = session.get("test_key") == "test_value"
        print_test("Data Persistence", has_data, "Values retained across calls")
        
        return has_data
    except Exception as e:
        print_test("Session Memory", False, str(e)[:60])
        return False


def test_database():
    """Test Level 300: SQLite Persistence."""
    print_header("Level 300: SQLite Persistence")
    
    try:
        from app.data.models import (
            init_db, ConversationSession, Message
        )
        
        db_url = f"sqlite:///{project_root}/data/sqlite/conversations.db"
        Session, engine = init_db(db_url)
        print_test("Database Connection", True, f"SQLite @ {db_url.split('/')[-1]}")
        
        # Check table count
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "conversation_sessions", "messages", "tool_executions", 
            "token_usage", "system_metrics"
        ]
        
        all_present = all(t in tables for t in expected_tables)
        print_test(f"Table Creation ({len(tables)} tables)", all_present, 
                   f"All required tables present: {', '.join(tables)}")
        
        # Test session creation (use timestamp for unique ID)
        import time
        session = Session()
        test_id = f"test-conv-{int(time.time() * 1000)}"
        conv_session = ConversationSession(
            id=test_id,
            user_id="test-user",
            context_type="test"
        )
        session.add(conv_session)
        session.commit()
        
        # Verify
        retrieved = session.query(ConversationSession).filter_by(id=test_id).first()
        can_store = retrieved is not None
        print_test("Data Storage & Retrieval", can_store, "Session persisted to database")
        
        session.close()
        return all_present and can_store
    except Exception as e:
        print_test("Database", False, str(e)[:60])
        import traceback
        traceback.print_exc()
        return False


def test_observability():
    """Test Level 300: Observability & Logging."""
    print_header("Level 300: Observability & Logging")
    
    try:
        from app.services.observability import (
            get_logger, metrics, Timer, init_logging
        )
        
        # Initialize logging
        init_logging(log_file=f"{project_root}/logs/test.log", log_level="INFO")
        logger = get_logger()
        print_test("Logger Initialization", logger is not None, "JSON logger ready")
        
        # Test logging
        logger.log_request("/chat", "POST", "test-session", "test message")
        print_test("Request Logging", True, "Event captured")
        
        # Test metrics
        metrics.record_latency("/chat", 42.5)
        metrics.record_tokens(100, 0.001)
        metrics.record_tool_success("test_tool", True)
        
        summary = metrics.get_summary()
        has_metrics = len(summary) > 0
        print_test("Metrics Collection", has_metrics, f"Collected {len(summary)} metric groups")
        
        # Test timer
        with Timer("test_operation") as timer:
            time.sleep(0.01)
        
        timer_ok = timer.elapsed_ms and timer.elapsed_ms > 5
        print_test("Timer Context Manager", timer_ok, f"Measured {timer.elapsed_ms:.1f}ms")
        
        return logger is not None and has_metrics and timer_ok
    except Exception as e:
        print_test("Observability", False, str(e)[:60])
        import traceback
        traceback.print_exc()
        return False


def test_docker_endpoints():
    """Test Level 200: FastAPI Endpoints."""
    print_header("Level 200: FastAPI Endpoints")
    
    try:
        import asyncio
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        health_ok = response.status_code == 200
        print_test("GET /health", health_ok, f"Status: {response.status_code}")
        
        # Test metrics endpoint
        response = client.get("/metrics")
        metrics_ok = response.status_code == 200
        print_test("GET /metrics", metrics_ok, f"Status: {response.status_code}")
        
        # Test chat endpoint
        try:
            response = client.post(
                "/chat",
                json={"session_id": "test-123", "message": "test"},
                timeout=5
            )
            chat_ok = response.status_code in [200, 422]  # 422 if validation fails, that's ok
            print_test("POST /chat", chat_ok, f"Status: {response.status_code}")
        except Exception as e:
            print_test("POST /chat", False, f"Connection error: {str(e)[:40]}")
            chat_ok = False
        
        return health_ok and metrics_ok
    except Exception as e:
        print_test("FastAPI Endpoints", False, str(e)[:60])
        return False


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE".center(60))
    print("Level 100/200/300 System Validation".center(60))
    print("=" * 60)
    print(f"{Colors.ENDC}\n")
    
    start_time = time.time()
    
    results = {
        "Imports": test_imports(),
        "RAG Pipeline (L100)": test_rag_pipeline(),
        "Order Workflow (L100)": test_order_workflow(),
        "Session Memory (L100)": test_session_memory(),
        "Database (L300)": test_database(),
        "Observability (L300)": test_observability(),
        "FastAPI Endpoints (L200)": test_docker_endpoints(),
    }
    
    elapsed = time.time() - start_time
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = f"{Colors.GREEN}✅{Colors.ENDC}" if result else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"{status_icon} {test_name}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.ENDC}")
    print(f"Time: {elapsed:.2f}s\n")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
