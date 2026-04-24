#!/usr/bin/env python3
"""
Master Test Runner - Runs all test suites and generates a comprehensive report.

This script orchestrates:
1. Database initialization
2. Comprehensive system tests
3. Frontend integration tests
4. Summary report with all results
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


def run_command(cmd: str, description: str) -> tuple[bool, str]:
    """Run a command and return (success, output)."""
    print(f"\n⏳ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def main():
    """Run all tests."""
    project_root = Path(__file__).parent.parent
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "="*68 + "╗")
    print("║" + "MASTER TEST RUNNER".center(68) + "║")
    print("║" + "Level 100/200/300 Complete Test Suite".center(68) + "║")
    print("║" + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(68) + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.ENDC}")
    
    results = {}
    start_time = time.time()
    
    # Check if API is running
    print_section("Pre-Flight Check")
    
    import requests
    api_running = False
    print("Checking if API server is running on localhost:8000...")
    for attempt in range(3):
        try:
            requests.get("http://localhost:8000/health", timeout=1)
            api_running = True
            print(f"{Colors.GREEN}✅ API server is running{Colors.ENDC}")
            break
        except:
            if attempt < 2:
                print(f"   Attempt {attempt + 1}/3... waiting 2 seconds")
                time.sleep(2)
    
    if not api_running:
        print(f"{Colors.YELLOW}⚠️  API server is NOT running!{Colors.ENDC}")
        print("   Start it with: uvicorn app.main:app --reload")
        print("\n   Proceeding with offline tests only...\n")
    
    # Test 1: Database initialization
    print_section("Test 1: Database Initialization")
    
    success, output = run_command(
        f"cd {project_root} && python tests/setup_db.py",
        "Initializing SQLite database"
    )
    results["Database Init"] = success
    
    if success:
        print(f"{Colors.GREEN}✅ Database initialized successfully{Colors.ENDC}")
    else:
        print(f"{Colors.RED}❌ Database initialization failed{Colors.ENDC}")
        if "already" in output.lower():
            print(f"   (Database already exists - this is OK)")
            results["Database Init"] = True
    
    # Test 2: Comprehensive test suite
    print_section("Test 2: Comprehensive System Tests")
    
    success, output = run_command(
        f"cd {project_root} && python tests/test_core.py",
        "Running comprehensive test suite"
    )
    results["Comprehensive Tests"] = success
    
    # Parse test results
    if "7/7 tests passed" in output or "ALL TESTS PASSED" in output:
        print(f"{Colors.GREEN}✅ All comprehensive tests passed (7/7){Colors.ENDC}")
        print(f"   Tests included:")
        print(f"   • Imports validation")
        print(f"   • RAG Pipeline (Level 100)")
        print(f"   • Order Workflow (Level 100)")
        print(f"   • Session Memory (Level 100)")
        print(f"   • Database Persistence (Level 300)")
        print(f"   • Logging & Metrics (Level 300)")
        print(f"   • FastAPI Endpoints (Level 200)")
    else:
        print(f"{Colors.YELLOW}⚠️  Some comprehensive tests may have issues{Colors.ENDC}")
        # Show last 30 lines of output
        lines = output.split('\n')
        print("\n   Last test output:")
        for line in lines[-30:]:
            if line.strip():
                print(f"   {line}")
    
    # Test 3: Frontend integration tests (only if API is running)
    print_section("Test 3: Frontend Integration Tests")
    
    if api_running:
        success, output = run_command(
            f"cd {project_root} && python tests/test_integration.py",
            "Running frontend integration tests"
        )
        results["Frontend Integration"] = success
        
        if "8/8" in output or "ALL TESTS PASSED" in output:
            print(f"{Colors.GREEN}✅ All frontend integration tests passed (8/8){Colors.ENDC}")
            print(f"   Tests included:")
            print(f"   • Frontend Dependencies")
            print(f"   • Database Operations")
            print(f"   • Logging & Metrics")
            print(f"   • API Health Endpoint")
            print(f"   • API Metrics Endpoint")
            print(f"   • Chat Streaming")
            print(f"   • Order Workflow Integration")
            print(f"   • RAG Query Integration")
        else:
            print(f"{Colors.YELLOW}⚠️  Some frontend tests may have issues{Colors.ENDC}")
            lines = output.split('\n')
            print("\n   Last test output:")
            for line in lines[-30:]:
                if line.strip():
                    print(f"   {line}")
    else:
        print(f"{Colors.YELLOW}⏭️  Skipping (API server not running){Colors.ENDC}")
        print("   Start API with: uvicorn app.main:app --reload")
        results["Frontend Integration"] = None
    
    # Summary
    print_section("Test Summary")
    
    elapsed = time.time() - start_time
    
    total_tests = len([v for v in results.values() if v is not None])
    passed_tests = len([v for v in results.values() if v is True])
    skipped = len([v for v in results.values() if v is None])
    
    print(f"\n{'Test Category':<30} {'Result':<20} {'Status'}")
    print("-" * 70)
    
    for test_name, result in results.items():
        if result is None:
            status = f"{Colors.YELLOW}⏭️  SKIPPED{Colors.ENDC}"
        elif result:
            status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}"
        else:
            status = f"{Colors.RED}❌ FAIL{Colors.ENDC}"
        
        print(f"{test_name:<30} {status}")
    
    print("-" * 70)
    print(f"\nResults: {passed_tests}/{total_tests} test suites passed")
    if skipped > 0:
        print(f"         {skipped} test suites skipped (API not running)")
    print(f"Elapsed: {elapsed:.1f} seconds")
    
    # Final recommendation
    print("\n" + "="*70)
    
    if passed_tests == total_tests and skipped == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("🎉 ALL TESTS PASSED - PROJECT READY FOR DEPLOYMENT 🎉".center(70))
        print(f"{Colors.ENDC}")
        exit_code = 0
    elif passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("✅ OFFLINE TESTS PASSED - API TESTS AVAILABLE WHEN SERVER RUNS".center(70))
        print(f"{Colors.ENDC}")
        exit_code = 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}")
        print("⚠️  SOME TESTS FAILED - REVIEW OUTPUT ABOVE".center(70))
        print(f"{Colors.ENDC}")
        exit_code = 1
    
    print("="*70 + "\n")
    
    # Additional information
    print(f"{Colors.CYAN}Next Steps:{Colors.ENDC}")
    print("  1. Fix any failed tests (see output above)")
    print("  2. Review TESTING_GUIDE.md for detailed test procedures")
    print("  3. Run Streamlit UI: streamlit run frontend/streamlit_app.py")
    print("  4. Deploy to cloud: Render.com or Railway.app (optional)")
    print()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
