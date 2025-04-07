#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test the packaged CountyDataSync executable

This script tests if the packaged CountyDataSync executable works properly
by running it with test parameters and verifying the output.

Usage:
    python test_packaged_executable.py [--exe-path PATH] [--test-mode basic|full]
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
import shutil
import time

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test packaged CountyDataSync executable')
    
    # Default executable path based on platform
    default_exe = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
    
    parser.add_argument('--exe-path', type=str, default=default_exe,
                       help=f'Path to the executable (default: {default_exe})')
    parser.add_argument('--test-mode', choices=['basic', 'full'], default='basic',
                       help='Test mode: basic or full (default: basic)')
    
    return parser.parse_args()

def check_executable(exe_path):
    """Check if the executable exists and is runnable."""
    print(f"Checking executable at {exe_path}...")
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    if not os.access(exe_path, os.X_OK) and platform.system() != 'Windows':
        print(f"❌ Executable does not have execute permissions")
        return False
    
    print(f"✓ Executable found and has appropriate permissions")
    return True

def setup_test_environment():
    """Set up a temporary test environment."""
    print("Setting up test environment...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="countydatasync_test_")
    print(f"✓ Created temporary directory: {temp_dir}")
    
    # Create required subdirectories
    for subdir in ['data', 'output', 'logs', 'config']:
        os.makedirs(os.path.join(temp_dir, subdir), exist_ok=True)
    
    # Create a test .env file
    env_path = os.path.join(temp_dir, '.env')
    with open(env_path, 'w') as f:
        f.write("# Test environment configuration\n")
        f.write("USE_TEST_DATA=true\n")
        f.write("TEST_MODE=true\n")
        f.write("LOG_LEVEL=DEBUG\n")
    
    return temp_dir

def run_basic_test(exe_path, test_dir):
    """Run a basic test of the executable."""
    print("\nRunning basic test...")
    
    try:
        # Run the executable with --help to check if it works
        print("Testing --help option...")
        help_result = subprocess.run([exe_path, '--help'], 
                                    cwd=test_dir,
                                    capture_output=True, 
                                    text=True,
                                    timeout=30)
        
        if help_result.returncode != 0:
            print(f"❌ Help test failed with return code {help_result.returncode}")
            print("--- STDOUT ---")
            print(help_result.stdout)
            print("--- STDERR ---")
            print(help_result.stderr)
            return False
        
        print("✓ Help test passed")
        
        # Run with --version
        print("Testing --version option...")
        version_result = subprocess.run([exe_path, '--version'], 
                                       cwd=test_dir,
                                       capture_output=True, 
                                       text=True,
                                       timeout=30)
        
        if version_result.returncode != 0:
            print(f"❌ Version test failed with return code {version_result.returncode}")
            print("--- STDOUT ---")
            print(version_result.stdout)
            print("--- STDERR ---")
            print(version_result.stderr)
            return False
        
        print("✓ Version test passed")
        
        # Run with --test flag (assuming the app has this)
        print("Testing built-in test mode...")
        test_result = subprocess.run([exe_path, '--test'], 
                                    cwd=test_dir,
                                    capture_output=True, 
                                    text=True,
                                    timeout=60)
        
        if test_result.returncode != 0:
            print(f"❌ Built-in test failed with return code {test_result.returncode}")
            print("--- STDOUT ---")
            print(test_result.stdout)
            print("--- STDERR ---")
            print(test_result.stderr)
            return False
        
        print("✓ Built-in test passed")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

def run_full_test(exe_path, test_dir):
    """Run a comprehensive test of the executable."""
    print("\nRunning full test suite...")
    
    if not run_basic_test(exe_path, test_dir):
        return False
    
    try:
        # Run the executable with test data
        print("\nTesting with sample data processing...")
        
        # Copy test data if available
        if os.path.exists('tests/data'):
            shutil.copytree('tests/data', os.path.join(test_dir, 'data'), dirs_exist_ok=True)
        
        # Run the actual data processing test
        process_result = subprocess.run([exe_path, '--process', 'test_dataset'], 
                                      cwd=test_dir,
                                      capture_output=True, 
                                      text=True,
                                      timeout=120)
        
        if process_result.returncode != 0:
            print(f"❌ Data processing test failed with return code {process_result.returncode}")
            print("--- STDOUT ---")
            print(process_result.stdout)
            print("--- STDERR ---")
            print(process_result.stderr)
            return False
        
        # Check if output files were created
        output_files = os.listdir(os.path.join(test_dir, 'output'))
        if not output_files:
            print("❌ No output files were created")
            return False
        
        print(f"✓ Data processing test passed, generated {len(output_files)} output files")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Full test timed out (120 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error during full test: {str(e)}")
        return False

def cleanup_test_environment(test_dir):
    """Clean up the temporary test environment."""
    print(f"\nCleaning up test environment at {test_dir}...")
    try:
        shutil.rmtree(test_dir)
        print("✓ Test environment cleaned up")
    except Exception as e:
        print(f"⚠️ Failed to clean up test environment: {str(e)}")

def main():
    """Main function."""
    args = parse_arguments()
    
    print("=" * 60)
    print("CountyDataSync Packaged Executable Test")
    print("=" * 60)
    
    if not check_executable(args.exe_path):
        return 1
    
    test_dir = setup_test_environment()
    
    try:
        if args.test_mode == 'basic':
            success = run_basic_test(args.exe_path, test_dir)
        else:  # full
            success = run_full_test(args.exe_path, test_dir)
        
        print("\n" + "=" * 60)
        if success:
            print("✅ All tests passed! The packaged executable is working properly.")
        else:
            print("❌ Tests failed. Please check the issues above.")
        
        return 0 if success else 1
        
    finally:
        cleanup_test_environment(test_dir)

if __name__ == "__main__":
    sys.exit(main())