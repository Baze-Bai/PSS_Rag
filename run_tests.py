#!/usr/bin/env python3
"""
Test runner for PSS RAG System
Runs comprehensive test suite with reporting
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_command(command, description):
    """Run command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(command)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        end_time = time.time()
        
        print(f"✅ SUCCESS ({end_time - start_time:.2f}s)")
        if result.stdout:
            print("STDOUT:", result.stdout[:500])
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print(f"❌ FAILED ({end_time - start_time:.2f}s)")
        print("STDERR:", e.stderr[:500])
        print("STDOUT:", e.stdout[:500])
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("DEPENDENCY CHECK")
    
    required_packages = [
        'pytest', 'streamlit', 'boto3', 'faiss-cpu', 
        'sentence-transformers', 'python-dotenv', 'tenacity'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT FOUND")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies satisfied")
    return True

def run_unit_tests():
    """Run unit tests"""
    print_header("UNIT TESTS")
    
    test_commands = [
        {
            "cmd": ["python", "-m", "pytest", "tests/test_rag_system.py::TestConfig", "-v"],
            "desc": "Configuration Tests"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/test_rag_system.py::TestSecurityManager", "-v"],
            "desc": "Security Tests"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/test_rag_system.py::TestLLMService", "-v"],
            "desc": "LLM Service Tests"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/test_rag_system.py::TestRAGLogger", "-v"],
            "desc": "Logger Tests"
        }
    ]
    
    results = []
    for test in test_commands:
        success = run_command(test["cmd"], test["desc"])
        results.append((test["desc"], success))
    
    return results

def run_integration_tests():
    """Run integration tests"""
    print_header("INTEGRATION TESTS")
    
    test_commands = [
        {
            "cmd": ["python", "-m", "pytest", "tests/test_rag_system.py::TestIntegration", "-v"],
            "desc": "Integration Tests"
        }
    ]
    
    results = []
    for test in test_commands:
        success = run_command(test["cmd"], test["desc"])
        results.append((test["desc"], success))
    
    return results

def run_security_tests():
    """Run security-specific tests"""
    print_header("SECURITY TESTS")
    
    # Test input validation
    test_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "javascript:alert('test')",
        "eval(malicious_code)",
        "a" * 1001  # Too long input
    ]
    
    print("🔍 Testing input validation with malicious inputs...")
    
    try:
        from utils.security import security_manager
        
        for test_input in test_inputs:
            is_valid, message = security_manager.validate_input(test_input)
            if is_valid:
                print(f"❌ SECURITY ISSUE: Input '{test_input[:50]}...' was not blocked")
                return False
            else:
                print(f"✅ Blocked: {test_input[:30]}...")
        
        print("✅ All malicious inputs properly blocked")
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {str(e)}")
        return False

def run_performance_tests():
    """Run basic performance tests"""
    print_header("PERFORMANCE TESTS")
    
    try:
        from config import Config
        
        # Test configuration loading
        start_time = time.time()
        validation = Config.validate_config()
        config_time = time.time() - start_time
        
        print(f"⏱️ Configuration validation: {config_time:.3f}s")
        
        if config_time > 1.0:
            print("⚠️ Configuration loading is slow")
        else:
            print("✅ Configuration loading performance OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return False

def generate_test_report(unit_results, integration_results, security_passed, performance_passed):
    """Generate comprehensive test report"""
    print_header("TEST REPORT")
    
    total_tests = len(unit_results) + len(integration_results) + 2  # +2 for security and performance
    passed_tests = 0
    
    print(f"Test execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    print("\n📊 DETAILED RESULTS:")
    
    # Unit test results
    print("\n🔧 Unit Tests:")
    for test_name, passed in unit_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if passed:
            passed_tests += 1
    
    # Integration test results
    print("\n🔗 Integration Tests:")
    for test_name, passed in integration_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if passed:
            passed_tests += 1
    
    # Security test results
    security_status = "✅ PASS" if security_passed else "❌ FAIL"
    print(f"\n🔒 Security Tests: {security_status}")
    if security_passed:
        passed_tests += 1
    
    # Performance test results
    performance_status = "✅ PASS" if performance_passed else "❌ FAIL"
    print(f"\n⚡ Performance Tests: {performance_status}")
    if performance_passed:
        passed_tests += 1
    
    # Summary
    print(f"\n📈 SUMMARY:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} TEST(S) FAILED")
        return False

def main():
    """Main test runner"""
    print_header("PSS RAG SYSTEM - COMPREHENSIVE TEST SUITE")
    print(f"Starting test execution at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required packages.")
        sys.exit(1)
    
    # Run test suites
    unit_results = run_unit_tests()
    integration_results = run_integration_tests()
    security_passed = run_security_tests()
    performance_passed = run_performance_tests()
    
    # Generate report
    all_passed = generate_test_report(
        unit_results, 
        integration_results, 
        security_passed, 
        performance_passed
    )
    
    # Exit with appropriate code
    if all_passed:
        print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test suite completed with failures!")
        sys.exit(1)

if __name__ == "__main__":
    main() 