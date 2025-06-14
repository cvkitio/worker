#!/usr/bin/env python3
"""
Test runner script for cvkitworker.

This script provides easy commands to run different types of tests:
- Unit tests: Fast tests that test individual components
- Integration tests: Slower tests that test end-to-end functionality
- All tests: Run everything (not recommended for CI)
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n🧪 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")
    
    return result.returncode


def get_base_cmd():
    """Get the base pytest command with common options."""
    return [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short"
    ]


def run_unit_tests(coverage=False, verbose=False):
    """Run unit tests (excluding integration and slow tests)."""
    cmd = get_base_cmd()
    cmd.extend([
        "-m", "not integration and not slow",
        "--timeout=30"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/cvkitworker", 
            "--cov-report=xml", 
            "--cov-report=html",
            "--cov-report=term"
        ])
    
    if verbose:
        cmd.append("-s")
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(timeout=300):
    """Run integration tests (may take longer)."""
    cmd = get_base_cmd()
    cmd.extend([
        "-m", "integration",
        f"--timeout={timeout}",
        "--tb=long"  # More verbose output for integration failures
    ])
    
    return run_command(cmd, "Integration Tests")


def run_video_tests(timeout=600):
    """Run video processing tests (subset of integration tests)."""
    cmd = get_base_cmd()
    cmd.extend([
        "-m", "video", 
        f"--timeout={timeout}",
        "--tb=long"
    ])
    
    return run_command(cmd, "Video Processing Tests")


def run_slow_tests(timeout=300):
    """Run slow tests (includes video creation, etc.)."""
    cmd = get_base_cmd()
    cmd.extend([
        "-m", "slow",
        f"--timeout={timeout}"
    ])
    
    return run_command(cmd, "Slow Tests")


def run_all_tests(coverage=False):
    """Run all tests (unit + integration + slow)."""
    cmd = get_base_cmd()
    cmd.extend([
        "--timeout=600",
        "--tb=short"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/cvkitworker", 
            "--cov-report=xml",
            "--cov-report=term"
        ])
    
    return run_command(cmd, "All Tests")


def run_fast_tests():
    """Run only the fastest tests for quick validation."""
    cmd = get_base_cmd()
    cmd.extend([
        "-m", "not integration and not slow and not video",
        "--timeout=30",
        "-q"  # Quiet output
    ])
    
    return run_command(cmd, "Fast Tests")


def list_test_markers():
    """List available test markers."""
    print("\n📋 Available Test Markers:")
    print("=" * 40)
    markers = {
        "unit": "Fast tests of individual components",
        "integration": "End-to-end tests (slower)",
        "video": "Video processing tests (subset of integration)",
        "slow": "Tests that create videos or take significant time"
    }
    
    for marker, description in markers.items():
        print(f"  {marker:12} - {description}")
    
    print("\n📊 Test Categories:")
    print("=" * 40)
    categories = {
        "Fast": "not integration and not slow and not video",
        "Unit": "not integration and not slow", 
        "Integration": "integration",
        "Video": "video",
        "Slow": "slow"
    }
    
    for category, expression in categories.items():
        print(f"  {category:12} - pytest -m \"{expression}\"")


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Test runner for cvkitworker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --unit                    # Run unit tests only
  %(prog)s --integration             # Run integration tests  
  %(prog)s --unit --coverage         # Run unit tests with coverage
  %(prog)s --fast                    # Run fastest tests only
  %(prog)s --video                   # Run video processing tests
  %(prog)s --all                     # Run all tests (slow!)
  %(prog)s --list                    # Show available test markers
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--unit", action="store_true", 
                      help="Run unit tests (fast, excludes integration)")
    group.add_argument("--integration", action="store_true",
                      help="Run integration tests (slower)")
    group.add_argument("--video", action="store_true",
                      help="Run video processing tests")
    group.add_argument("--slow", action="store_true", 
                      help="Run slow tests")
    group.add_argument("--fast", action="store_true",
                      help="Run only the fastest tests")
    group.add_argument("--all", action="store_true",
                      help="Run all tests (not recommended for CI)")
    group.add_argument("--list", action="store_true",
                      help="List available test markers and categories")
    
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report (only for unit/all tests)")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--timeout", type=int, default=None,
                       help="Override default timeout (seconds)")
    
    args = parser.parse_args()
    
    if args.list:
        list_test_markers()
        return 0
    
    # Ensure we're in the right directory
    if not Path("tests").exists() or not Path("src").exists():
        print("❌ Error: Must run from project root directory")
        print("   (Should contain 'tests/' and 'src/' directories)")
        return 1
    
    print(f"🚀 CVKit Worker Test Runner")
    print(f"Working directory: {Path.cwd()}")
    
    exit_code = 0
    
    try:
        if args.unit:
            exit_code = run_unit_tests(coverage=args.coverage, verbose=args.verbose)
        elif args.integration:
            timeout = args.timeout or 300
            exit_code = run_integration_tests(timeout=timeout)
        elif args.video:
            timeout = args.timeout or 600
            exit_code = run_video_tests(timeout=timeout)
        elif args.slow:
            timeout = args.timeout or 300
            exit_code = run_slow_tests(timeout=timeout)
        elif args.fast:
            exit_code = run_fast_tests()
        elif args.all:
            exit_code = run_all_tests(coverage=args.coverage)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        exit_code = 1
    
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("🎉 All tests completed successfully!")
    else:
        print("💥 Some tests failed. Check output above.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())