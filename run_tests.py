#!/usr/bin/env python3
"""
Comprehensive test runner for ConceptNet MCP utility modules.

This script runs all tests with coverage reporting and provides detailed
output about test results, performance, and coverage statistics.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def setup_environment():
    """Set up the test environment."""
    # Add src to Python path
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    sys.path.insert(0, str(src_dir))
    
    # Set environment variables for testing
    os.environ['PYTHONPATH'] = str(src_dir)
    os.environ['PYTEST_CURRENT_TEST'] = 'true'


def run_pytest(test_args=None, coverage=True, verbose=True):
    """Run pytest with specified arguments."""
    cmd = ['python', '-m', 'pytest']
    
    if test_args:
        cmd.extend(test_args)
    else:
        # Default test arguments
        cmd.extend(['tests/', '-v'])
    
    if coverage:
        cmd.extend([
            '--cov=src/conceptnet_mcp/utils',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml'
        ])
    
    if verbose:
        cmd.extend(['-v', '--tb=short'])
    
    # Add markers and filtering
    cmd.extend([
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest:")
        print("pip install pytest pytest-cov")
        return 1


def run_unit_tests():
    """Run only unit tests."""
    return run_pytest([
        'tests/unit/',
        '-m', 'unit or not integration',
        '-v'
    ])


def run_integration_tests():
    """Run only integration tests."""
    return run_pytest([
        'tests/',
        '-m', 'integration',
        '-v',
        'test_utils_integration.py'
    ])


def run_performance_tests():
    """Run performance tests."""
    return run_pytest([
        'tests/',
        '-m', 'performance',
        '-v',
        '--durations=10'
    ])


def run_security_tests():
    """Run security-related tests."""
    return run_pytest([
        'tests/',
        '-m', 'security',
        '-v'
    ])


def run_all_tests():
    """Run all tests with comprehensive coverage."""
    return run_pytest([
        'tests/',
        'test_utils_integration.py',
        '-v',
        '--durations=10'
    ])


def run_quick_tests():
    """Run a quick subset of tests (no slow tests)."""
    return run_pytest([
        'tests/',
        'test_utils_integration.py',
        '-m', 'not slow',
        '-x',  # Stop on first failure
        '--tb=line'
    ])


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['pytest', 'pytest-cov']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Run ConceptNet MCP utility tests')
    parser.add_argument(
        '--type', 
        choices=['all', 'unit', 'integration', 'performance', 'security', 'quick'],
        default='all',
        help='Type of tests to run'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage reporting'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Run tests with minimal output'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        help='Run tests matching specific pattern'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Run tests from specific file'
    )
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    print("ConceptNet MCP Utility Tests")
    print("=" * 60)
    
    # Handle specific file or pattern
    if args.file:
        return run_pytest([args.file], coverage=not args.no_coverage, verbose=not args.quiet)
    
    if args.pattern:
        return run_pytest(['-k', args.pattern], coverage=not args.no_coverage, verbose=not args.quiet)
    
    # Run tests based on type
    if args.type == 'unit':
        return_code = run_unit_tests()
    elif args.type == 'integration':
        return_code = run_integration_tests()
    elif args.type == 'performance':
        return_code = run_performance_tests()
    elif args.type == 'security':
        return_code = run_security_tests()
    elif args.type == 'quick':
        return_code = run_quick_tests()
    else:  # all
        return_code = run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    if return_code == 0:
        print("✅ All tests passed!")
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
        print(f"Exit code: {return_code}")
    
    return return_code


if __name__ == '__main__':
    sys.exit(main())