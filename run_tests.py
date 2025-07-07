#!/usr/bin/env python3
"""Test runner script with various options."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list) -> int:
    """Run a command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)
    result = subprocess.run(cmd)
    print("-" * 80)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run Trapper Keeper tests")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "e2e", "performance"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure",
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for changes and re-run tests",
    )
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files or directories to run",
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["pytest"]
    
    # Add type-specific markers
    if args.type != "all":
        cmd.extend(["-m", args.type])
    
    # Add coverage options
    if args.coverage:
        cmd.extend([
            "--cov=trapper_keeper",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
        ])
    
    # Add verbose flag
    if args.verbose:
        cmd.append("-vv")
    
    # Add failfast
    if args.failfast:
        cmd.append("-x")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add benchmark options
    if args.benchmark:
        cmd.extend([
            "--benchmark-only",
            "--benchmark-verbose",
            "--benchmark-sort=time",
            "--benchmark-save=benchmark",
        ])
    
    # Add specific tests
    if args.tests:
        cmd.extend(args.tests)
    
    # Run tests
    if args.watch:
        # Use pytest-watch
        watch_cmd = ["ptw", "--"] + cmd[1:]  # Remove 'pytest' from command
        return run_command(watch_cmd)
    else:
        return run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())