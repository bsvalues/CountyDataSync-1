#!/usr/bin/env python3
"""
Test the packaged executable for CountyDataSync.

This script verifies that the packaged executable works correctly by running it with test data.
"""
import os
import sys
import time
import tempfile
import subprocess
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestPackagedExecutable')

def find_executable():
    """Find the CountyDataSync executable in the dist directory."""
    dist_dir = Path('dist')
    
    if not dist_dir.exists():
        logger.error("dist directory not found. Build executable first.")
        return None
    
    executables = list(dist_dir.glob('CountyDataSync*'))
    
    if not executables:
        logger.error("No executable found in dist directory. Build executable first.")
        return None
    
    executable = executables[0]
    logger.info(f"Found executable: {executable}")
    return executable

def create_test_environment():
    """Create a test environment with temporary directories."""
    test_dir = tempfile.mkdtemp(prefix='countydatasync_test_')
    
    # Create subdirectories
    output_dir = os.path.join(test_dir, 'output')
    logs_dir = os.path.join(test_dir, 'logs')
    
    os.makedirs(output_dir)
    os.makedirs(logs_dir)
    
    logger.info(f"Created test environment in {test_dir}")
    
    return {
        'test_dir': test_dir,
        'output_dir': output_dir,
        'logs_dir': logs_dir,
    }

def run_test(executable, env):
    """Run the executable in test mode."""
    logger.info("Running executable in test mode...")
    
    # Set environment variables for the test
    test_env = os.environ.copy()
    test_env['USE_TEST_DATA'] = 'true'
    
    # Command to run the executable
    cmd = [
        executable,
        '--test-data',
        '--output-dir', env['output_dir'],
        '--verbose',
    ]
    
    try:
        process = subprocess.run(
            cmd,
            env=test_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,  # 2 minute timeout
        )
        
        logger.info(f"Executable returned with code: {process.returncode}")
        
        if process.returncode == 0:
            logger.info("Executable ran successfully")
            logger.info("Output:")
            for line in process.stdout.splitlines()[-20:]:  # Show last 20 lines of output
                logger.info(f"  {line}")
            return True
        else:
            logger.error("Executable failed")
            logger.error("Error output:")
            logger.error(process.stderr)
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("Executable timed out after 120 seconds")
        return False
    
    except Exception as e:
        logger.error(f"Error running executable: {e}")
        return False

def check_output_files(env):
    """Check if output files were created."""
    logger.info("Checking output files...")
    
    output_dir = Path(env['output_dir'])
    
    # List files in output directory
    files = list(output_dir.glob('*'))
    
    if not files:
        logger.error("No output files found")
        return False
    
    logger.info(f"Found {len(files)} output files:")
    for file in files:
        file_size = file.stat().st_size / 1024  # Convert to KB
        logger.info(f"  {file.name} ({file_size:.2f} KB)")
    
    return True

def cleanup(env):
    """Clean up the test environment."""
    logger.info(f"Cleaning up test environment: {env['test_dir']}")
    
    try:
        shutil.rmtree(env['test_dir'])
        logger.info("Test environment cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up test environment: {e}")

def main():
    """Main entry point."""
    logger.info("=== Testing Packaged Executable for CountyDataSync ===")
    
    # Find the executable
    executable = find_executable()
    if not executable:
        return 1
    
    # Create test environment
    env = create_test_environment()
    
    try:
        # Run the test
        success = run_test(executable, env)
        
        if success:
            # Check output files
            output_files_ok = check_output_files(env)
            
            if output_files_ok:
                logger.info("Test completed successfully!")
                return 0
            else:
                logger.error("Test failed: Output files not found or invalid")
                return 1
        else:
            logger.error("Test failed: Executable returned non-zero exit code")
            return 1
    
    finally:
        # Clean up
        cleanup(env)

if __name__ == "__main__":
    sys.exit(main())