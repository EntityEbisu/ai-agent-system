#!/usr/bin/env python3
"""
Integration test for frontend/Streamlit app with backend API.

This script validates:
1. API server is responsive
2. Streamlit UI components are importable
3. API endpoints return expected responses
4. Chat streaming works correctly
5. Metrics can be retrieved
"""

import sys
import time
import json
from pathlib import Path
from subprocess import Popen, PIPE

import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


def print_test(name: str, status: bool, details: str = ""):
    """Print test result."""
    icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
    print(f"{icon} {name}")
    if details:
        print(f"   {Colors.YELLOW}→{Colors.ENDC} {details}")


def test_streamlit_imports():
    """Test that Streamlit and required frontend libraries can be imported."""
    print_header("Frontend: Import Validation")
    
    all_good = True
    
    imports = {
        "streamlit": "st",
        "requests": "requests",
        "json": "json",
    }
    
    for module, alias in imports.items():
        try:
            __import__(module)
            print_test(f"Import {module}", True, "Available")
        except ImportError as e:
            print_test(f"Import {module}", False, str(e))
            all_good = False
    
    return all_good


def test_api_health(api_url="http://localhost:8000", timeout=2):
    """Test API health endpoint."""
    print_header("Backend API: Health Check")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            print_test("GET /health", True, f"Status: {response.status_code}")
            print_test("Response Format", "status" in data and "version" in data, 
                      f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_test("GET /health", False, f"Status: {response.status_code}")
            return False
    except requests.ConnectionError:
        print_test("GET /health", False, "API server not running on localhost:8000")
        return False
    except Exception as e:
        print_test("GET /health", False, str(e))
        return False


def test_api_metrics(api_url="http://localhost:8000", timeout=2):
    """Test API metrics endpoint."""
    print_header("Backend API: Metrics Endpoint")
    
    try:
        response = requests.get(f"{api_url}/metrics", timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            is_dict = isinstance(data, dict)
            
            print_test("GET /metrics", response.status_code == 200, 
                      f"Status: {response.status_code}")
            print_test("Response Format", is_dict, 
                      f"Response is dict (not list): {type(data).__name__}")
            
            # Metrics can be empty initially, but should be a dict
            return is_dict
        else:
            print_test("GET /metrics", False, f"Status: {response.status_code}")
            return False
    except requests.ConnectionError:
        print_test("GET /metrics", False, "API server not running")
        return False
    except Exception as e:
        print_test("GET /metrics", False, str(e))
        return False


def test_chat_endpoint(api_url="http://localhost:8000", timeout=30):
    """Test POST /chat endpoint with streaming."""
    print_header("Backend API: Chat Endpoint (Streaming)")
    
    try:
        payload = {
            "session_id": "test-frontend-123",
            "message": "Where is my order?"
        }
        
        response = requests.post(
            f"{api_url}/chat",
            json=payload,
            timeout=timeout,
            stream=True
        )
        
        if response.status_code != 200:
            print_test("POST /chat", False, f"Status: {response.status_code}")
            return False
        
        print_test("POST /chat", True, f"Status: {response.status_code}")
        
        # Verify streaming response format
        tokens = []
        error_lines = 0
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "token" in data:
                        tokens.append(data["token"])
                    elif "error" in data:
                        return False
                except json.JSONDecodeError:
                    error_lines += 1
        
        full_response = "".join(tokens)
        
        print_test("Streaming Format", len(tokens) > 0, 
                  f"Received {len(tokens)} tokens")
        print_test("Response Content", len(full_response) > 0, 
                  f"Response: '{full_response[:80]}'...")
        print_test("JSON Parsing", error_lines == 0, 
                  f"Parsed {len(tokens)} valid JSON lines")
        
        return len(tokens) > 0 and len(full_response) > 0
    except requests.ConnectionError:
        print_test("POST /chat", False, "API server not running")
        return False
    except Exception as e:
        print_test("POST /chat", False, str(e))
        return False


def test_chat_order_workflow(api_url="http://localhost:8000", timeout=30):
    """Test complete order workflow via chat API."""
    print_header("Backend API: Order Workflow (Full Flow)")
    
    try:
        session_id = "test-workflow-frontend"
        steps = [
            ("Where is my order?", "name"),          # Should ask for name
            ("Alice Nguyen", "SSN"),                 # Should ask for SSN
            ("1234", "YYYY-MM-DD"),                  # Should ask for DOB
            ("1990-01-01", "shipped"),               # Should return order status
        ]
        
        all_passed = True
        
        for i, (message, expected_keyword) in enumerate(steps, 1):
            try:
                response = requests.post(
                    f"{api_url}/chat",
                    json={"session_id": session_id, "message": message},
                    timeout=timeout,
                    stream=True
                )
                
                tokens = []
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "token" in data:
                                tokens.append(data["token"])
                        except json.JSONDecodeError:
                            pass
                
                full_response = "".join(tokens)
                has_keyword = expected_keyword.lower() in full_response.lower()
                
                print_test(f"Step {i}: {message[:40]}", has_keyword,
                          f"Response includes '{expected_keyword}'")
                
                if not has_keyword:
                    print(f"   Full response: {full_response[:100]}")
                    all_passed = False
                    
            except Exception as e:
                print_test(f"Step {i}: {message[:40]}", False, str(e))
                all_passed = False
        
        return all_passed
    except Exception as e:
        print_test("Order Workflow", False, str(e))
        return False


def test_rag_query(api_url="http://localhost:8000", timeout=30):
    """Test RAG query via chat API."""
    print_header("Backend API: RAG Query (Document Retrieval)")
    
    try:
        session_id = "test-rag-frontend"
        message = "What are the business risks mentioned in the document?"
        
        response = requests.post(
            f"{api_url}/chat",
            json={"session_id": session_id, "message": message},
            timeout=timeout,
            stream=True
        )
        
        if response.status_code != 200:
            print_test("RAG Query", False, f"Status: {response.status_code}")
            return False
        
        tokens = []
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "token" in data:
                        tokens.append(data["token"])
                except json.JSONDecodeError:
                    pass
        
        full_response = "".join(tokens)
        has_content = len(full_response) > 10
        
        print_test("RAG Query", response.status_code == 200, 
                  f"Status: {response.status_code}")
        print_test("Response Content", has_content,
                  f"Response length: {len(full_response)} chars")
        print_test("Response Preview", has_content,
                  f"'{full_response[:80]}'...")
        
        return has_content
    except requests.ConnectionError:
        print_test("RAG Query", False, "API server not running")
        return False
    except Exception as e:
        print_test("RAG Query", False, str(e))
        return False


def test_database_persistence(timeout=2):
    """Test that database is working and can store data."""
    print_header("Database: SQLite Persistence")
    
    try:
        from app.data.models import init_db, ConversationSession
        from sqlalchemy import inspect
        
        db_url = f"sqlite:///{project_root}/data/sqlite/conversations.db"
        Session, engine = init_db(db_url)
        
        # Check tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "conversation_sessions", "messages", "tool_executions",
            "token_usage", "system_metrics"
        ]
        
        all_present = all(t in tables for t in expected_tables)
        print_test("Database File", True, f"SQLite @ conversations.db")
        print_test(f"Tables ({len(tables)})", all_present,
                  f"Tables: {', '.join(tables)}")
        
        # Test data insertion
        session = Session()
        test_session = ConversationSession(
            id=f"test-frontend-db-{int(time.time())}",  # Use timestamp for uniqueness
            user_id="test-user",
            context_type="frontend_test"
        )
        session.add(test_session)
        session.commit()
        
        # Verify retrieval
        retrieved = session.query(ConversationSession).filter_by(
            id=test_session.id
        ).first()
        
        can_store = retrieved is not None
        print_test("Data Storage", can_store, "Session persisted")
        
        session.close()
        return all_present and can_store
        
    except Exception as e:
        print_test("Database", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_logging_output():
    """Test that logging is working and producing JSON output."""
    print_header("Observability: Logging & Metrics")
    
    try:
        from app.services.observability import get_logger, metrics, Timer
        
        # Test logger initialization
        logger = get_logger()
        logger_ok = logger is not None
        print_test("Logger Initialization", logger_ok, "JSON logger ready")
        
        # Test metrics
        metrics.record_latency("/chat", 42.5)
        metrics.record_tokens(100, 0.001)
        
        summary = metrics.get_summary()
        has_metrics = len(summary) > 0
        print_test("Metrics Collection", has_metrics,
                  f"Collected metrics: {list(summary.keys())}")
        
        # Test timer
        with Timer("test_op") as t:
            time.sleep(0.01)
        
        timer_ok = t.elapsed_ms is not None and t.elapsed_ms > 5
        print_test("Timer Measurement", timer_ok,
                  f"Measured {t.elapsed_ms:.1f}ms")
        
        return logger_ok and has_metrics and timer_ok
        
    except Exception as e:
        print_test("Logging & Metrics", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all frontend integration tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "="*68 + "╗")
    print("║" + "FRONTEND INTEGRATION TEST SUITE".center(68) + "║")
    print("║" + "Level 100/200/300 Frontend Validation".center(68) + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.ENDC}")
    
    # Check if API is running first
    print("\n⏳ Checking if API server is running...")
    api_running = False
    for attempt in range(3):
        try:
            requests.get("http://localhost:8000/health", timeout=1)
            api_running = True
            break
        except:
            if attempt < 2:
                print(f"   Attempt {attempt + 1}/3... waiting 2 seconds")
                time.sleep(2)
    
    if not api_running:
        print(f"\n{Colors.YELLOW}⚠️  API server is not running!{Colors.ENDC}")
        print("   Start it with: uvicorn app.main:app --reload")
        print("\n   Skipping API integration tests...")
        api_tests_passed = False
    else:
        print(f"{Colors.GREEN}✅ API server is running{Colors.ENDC}\n")
        api_tests_passed = True
    
    # Run tests
    results = {
        "Frontend Imports": test_streamlit_imports(),
        "Database": test_database_persistence(),
        "Logging & Metrics": test_logging_output(),
    }
    
    if api_tests_passed:
        results["API Health"] = test_api_health()
        results["API Metrics"] = test_api_metrics()
        results["Chat Endpoint"] = test_chat_endpoint()
        results["Order Workflow"] = test_chat_order_workflow()
        results["RAG Query"] = test_rag_query()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} test categories passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  SOME TESTS FAILED{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    exit(main())
