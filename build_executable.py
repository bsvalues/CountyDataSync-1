#!/usr/bin/env python3
"""
Build script for creating a standalone executable of CountyDataSync using PyInstaller.

Usage:
    python build_executable.py
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_prerequisites():
    """Check if all prerequisites are installed."""
    try:
        import PyInstaller
        logger.info(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        logger.error("PyInstaller is not installed. Please install it using 'pip install pyinstaller'.")
        return False

def generate_spec_file():
    """Generate or update the PyInstaller spec file."""
    if not os.path.exists('generate_spec.py'):
        logger.error("generate_spec.py not found. Cannot generate spec file.")
        return False
    
    logger.info("Generating spec file...")
    result = subprocess.run([sys.executable, 'generate_spec.py'], 
                            capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(result.stdout.strip())
        return True
    else:
        logger.error(f"Error generating spec file: {result.stderr.strip()}")
        return False

def build_executable():
    """Build the executable using PyInstaller."""
    spec_file = 'countydatasync.spec'
    if not os.path.exists(spec_file):
        logger.warning(f"Spec file {spec_file} not found.")
        success = generate_spec_file()
        if not success:
            logger.error("Failed to generate spec file. Cannot continue.")
            return False
    
    # Create build and dist directories if they don't exist
    Path('build').mkdir(exist_ok=True)
    Path('dist').mkdir(exist_ok=True)
    
    logger.info("Building executable with PyInstaller...")
    cmd = [
        'pyinstaller', 
        '--clean',                # Clean PyInstaller cache
        '--noconfirm',            # Replace output directory without confirmation
        spec_file                 # Use the spec file
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            # Find the executable in the dist directory
            dist_dir = Path('dist')
            executables = list(dist_dir.glob('CountyDataSync*'))
            
            if executables:
                executable_path = executables[0]
                logger.info(f"Build successful! Executable created: {executable_path}")
                
                # Make the executable executable on Unix-like systems
                if not sys.platform.startswith('win'):
                    executable_path.chmod(executable_path.stat().st_mode | 0o111)
                    logger.info(f"Made executable: {executable_path}")
                
                return True
            else:
                logger.error("Build completed but no executable was found in the dist directory.")
                return False
        else:
            logger.error(f"PyInstaller failed with error: {process.stderr.strip()}")
            return False
    
    except FileNotFoundError:
        logger.error("PyInstaller command not found. Make sure it's installed and in your PATH.")
        return False
    except Exception as e:
        logger.error(f"An error occurred during build: {e}")
        return False

def main():
    """Run the PyInstaller build process."""
    logger.info("Starting build process for CountyDataSync executable")
    
    # Check if PyInstaller is installed
    if not check_prerequisites():
        return 1
    
    # Build the executable
    if build_executable():
        logger.info("Build process completed successfully!")
        return 0
    else:
        logger.error("Build process failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())