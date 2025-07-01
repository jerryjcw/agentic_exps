#!/usr/bin/env python3
"""
Test Runner for Agentic Experiments Project

This script runs all the tests for the project, organized by test category.
It provides options for running specific test suites or all tests.
"""

import os
import sys
import unittest
import argparse
import warnings

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test modules
TEST_MODULES = {
    'wrapper': 'test_langchain_wrapper',
    'openai': 'test_openai_wrapper',
    'integration': 'test_integration', 
    'comparison': 'test_model_comparison',
    'maybe_append': 'test_maybe_append_user_content'
}


class ColoredTextTestResult(unittest.TextTestResult):
    """Test result class with colored output."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.verbosity = verbosity
        
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write("✅ ")
            self.stream.writeln(f"PASS: {self.getDescription(test)}")
        else:
            self.stream.write("✅")
            
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write("❌ ")
            self.stream.writeln(f"ERROR: {self.getDescription(test)}")
        else:
            self.stream.write("❌")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write("❌ ")
            self.stream.writeln(f"FAIL: {self.getDescription(test)}")
        else:
            self.stream.write("❌")
            
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write("⏭️  ")
            self.stream.writeln(f"SKIP: {self.getDescription(test)} ({reason})")
        else:
            self.stream.write("⏭️")


class ColoredTextTestRunner(unittest.TextTestRunner):
    """Test runner with colored output."""
    
    resultclass = ColoredTextTestResult
    
    def run(self, test):
        print(f"\n🧪 Running {test.countTestCases()} tests...")
        print("=" * 60)
        
        result = super().run(test)
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print(f"✅ Passed: {result.success_count}")
        print(f"❌ Failed: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        print(f"⏭️  Skipped: {len(result.skipped)}")
        print(f"🏁 Total: {result.testsRun}")
        
        if result.failures:
            print(f"\n❌ Failures ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"  - {test}")
                
        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"  - {test}")
                
        success_rate = (result.success_count / result.testsRun * 100) if result.testsRun > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if result.wasSuccessful():
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. See details above.")
            
        return result


def load_test_suite(module_name):
    """Load a test suite from a module."""
    try:
        module = __import__(f'tests.{module_name}', fromlist=[module_name])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        return suite
    except ImportError as e:
        print(f"⚠️  Could not import {module_name}: {e}")
        return unittest.TestSuite()
    except Exception as e:
        print(f"❌ Error loading {module_name}: {e}")
        return unittest.TestSuite()


def run_specific_tests(test_names, verbosity=2):
    """Run specific test suites."""
    suite = unittest.TestSuite()
    
    for test_name in test_names:
        if test_name in TEST_MODULES:
            module_name = TEST_MODULES[test_name]
            print(f"📦 Loading {test_name} tests from {module_name}...")
            test_suite = load_test_suite(module_name)
            suite.addTest(test_suite)
        else:
            print(f"⚠️  Unknown test suite: {test_name}")
            print(f"Available test suites: {', '.join(TEST_MODULES.keys())}")
    
    if suite.countTestCases() > 0:
        runner = ColoredTextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        print("❌ No tests to run!")
        return False


def run_all_tests(verbosity=2):
    """Run all available tests."""
    print("🚀 Running All Tests")
    print("=" * 60)
    
    suite = unittest.TestSuite()
    
    for test_name, module_name in TEST_MODULES.items():
        print(f"📦 Loading {test_name} tests...")
        test_suite = load_test_suite(module_name)
        suite.addTest(test_suite)
    
    if suite.countTestCases() > 0:
        runner = ColoredTextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        print("❌ No tests found!")
        return False


def check_environment():
    """Check if the test environment is properly set up."""
    print("🔍 Checking Test Environment...")
    
    issues = []
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            from gpt_caller import get_api_key
            api_key_path = os.path.join(project_root, 'config', 'apikey')
            api_key = get_api_key(file_path=api_key_path)
        except:
            pass
    
    if not api_key:
        issues.append("⚠️  No OPENAI_API_KEY found (some tests will be skipped)")
    else:
        print("✅ API key found")
    
    # Check for required packages
    try:
        import google.adk
        print("✅ Google ADK available")
    except ImportError:
        issues.append("❌ Google ADK not available")
    
    try:
        import langchain
        print("✅ LangChain available")
    except ImportError:
        issues.append("❌ LangChain not available")
    
    try:
        from tools.gadk.tools import AVAILABLE_TOOLS
        print(f"✅ Tools available ({len(AVAILABLE_TOOLS)} tools)")
    except ImportError:
        issues.append("⚠️  Tools not available (tool tests will be skipped)")
    
    if issues:
        print("\n⚠️  Environment Issues:")
        for issue in issues:
            print(f"  {issue}")
        print("\nSome tests may be skipped due to missing dependencies.")
    else:
        print("\n✅ Environment looks good!")
    
    return len([i for i in issues if i.startswith("❌")]) == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for agentic experiments project",
        epilog="""
Examples:
  python run_tests.py                     # Run all tests
  python run_tests.py wrapper             # Run only wrapper tests
  python run_tests.py integration comparison  # Run integration and comparison tests
  python run_tests.py --check-env         # Just check environment
  python run_tests.py --quiet             # Run with minimal output
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'tests', 
        nargs='*', 
        help=f"Specific test suites to run. Available: {', '.join(TEST_MODULES.keys())}"
    )
    parser.add_argument(
        '--check-env', 
        action='store_true',
        help="Check test environment and exit"
    )
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help="Run with minimal output"
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help="Run with detailed output"
    )
    
    args = parser.parse_args()
    
    # Set verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # Suppress warnings unless verbose
    if verbosity < 2:
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    print("🧪 Agentic Experiments Test Runner")
    print("=" * 60)
    
    # Check environment
    env_ok = check_environment()
    
    if args.check_env:
        return 0 if env_ok else 1
    
    print()
    
    # Run tests
    if args.tests:
        success = run_specific_tests(args.tests, verbosity)
    else:
        success = run_all_tests(verbosity)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())