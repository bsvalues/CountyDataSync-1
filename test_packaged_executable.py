#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test the packaged executable for CountyDataSync.

This script verifies that the packaged executable works correctly by running it with test data.
"""

import os
import platform
import subprocess
import sys
import tempfile
import shutil
import time


def find_executable():
    """Find the CountyDataSync executable in the dist directory."""
    # Get the executable name based on the platform
    exe_name = 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else '')
    exe_path = os.path.join('dist', exe_name)
    
    if not os.path.exists(exe_path):
        print(f"Error: Executable not found at {exe_path}")
        print("You need to build the executable first with 'python build_executable.py'")
        return None
    
    print(f"Found executable at {exe_path}")
    return exe_path


def create_test_environment():
    """Create a test environment with temporary directories."""
    print("Creating test environment...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix='countydatasync_test_')
    print(f"Created temporary directory: {temp_dir}")
    
    # Create subdirectories
    output_dir = os.path.join(temp_dir, 'output')
    logs_dir = os.path.join(temp_dir, 'logs')
    os.makedirs(output_dir)
    os.makedirs(logs_dir)
    
    # Return paths
    return {
        'temp_dir': temp_dir,
        'output_dir': output_dir,
        'logs_dir': logs_dir
    }


def run_test(executable, env):
    """Run the executable in test mode."""
    print("\nRunning test with packaged executable...")
    
    # Command to run with test data and verbose logging
    cmd = [
        executable,
        '--test-data',
        '--verbose',
        f'--output-dir={env["output_dir"]}',
        '--batch-size=100'
    ]
    
    # Run the executable
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        process = subprocess.run(
            cmd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Print output
        print(process.stdout)
        if process.stderr:
            print("Errors:")
            print(process.stderr)
        
        print("-" * 40)
        print("Test completed successfully!")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Test failed with error code {e.returncode}:")
        print(e.stdout)
        print(e.stderr)
        return False
    
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False


def check_output_files(env):
    """Check if output files were created."""
    print("\nChecking output files...")
    
    # Define expected file patterns
    expected_patterns = [
        '.gpkg',  # GeoPackage file
        '.db',    # SQLite database
        '.csv',   # CSV data file
        '.json'   # JSON output
    ]
    
    # Check for files in the output directory
    found_files = []
    for root, _, files in os.walk(env['output_dir']):
        for file in files:
            found_files.append(os.path.join(root, file))
    
    # Check if any expected file types were found
    found_patterns = []
    for pattern in expected_patterns:
        for file in found_files:
            if file.endswith(pattern):
                found_patterns.append(pattern)
                break
    
    # Report findings
    if found_files:
        print(f"Found {len(found_files)} files in output directory:")
        for file in found_files:
            print(f"  - {os.path.basename(file)}")
        
        missing_patterns = [p for p in expected_patterns if p not in found_patterns]
        if missing_patterns:
            print(f"\nWarning: Could not find files with patterns: {', '.join(missing_patterns)}")
        
        return len(found_patterns) > 0
    else:
        print("No output files found.")
        return False


def cleanup(env):
    """Clean up the test environment."""
    print("\nCleaning up test environment...")
    
    try:
        shutil.rmtree(env['temp_dir'])
        print(f"Removed temporary directory: {env['temp_dir']}")
    except Exception as e:
        print(f"Warning: Failed to clean up temporary directory: {str(e)}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("CountyDataSync Packaged Executable Test")
    print("=" * 60)
    
    # Find the executable
    executable = find_executable()
    if not executable:
        sys.exit(1)
    
    # Create test environment
    env = create_test_environment()
    
    try:
        # Run test
        if not run_test(executable, env):
            print("\nTest failed.")
            sys.exit(1)
        
        # Check output files
        if not check_output_files(env):
            print("\nTest failed: No expected output files found.")
            sys.exit(1)
        
        print("\nAll tests passed! The packaged executable is working correctly.")
    
    finally:
        # Clean up
        cleanup(env)


if __name__ == "__main__":
    main()