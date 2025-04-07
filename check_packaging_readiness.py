#!/usr/bin/env python3
"""
Check system readiness for packaging CountyDataSync.

This script verifies that all prerequisites are met for packaging the application.
"""
import os
import sys
import importlib
import subprocess
import platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CheckReadiness')

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    logger.info(f"Python version: {platform.python_version()}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        logger.error("Python 3.7 or higher is required")
        return False
    return True

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        logger.info(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        logger.error("PyInstaller is not installed. Please install it using 'pip install pyinstaller'.")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'pandas',
        'numpy',
        'geopandas',
        'shapely', 
        'psutil',
        'flask',
        'flask_sqlalchemy',
        'sqlalchemy',
        'pyodbc',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages using 'pip install <package>'")
        return False
    
    logger.info("All required packages are installed")
    return True

def check_project_structure():
    """Check if the project structure is valid for packaging."""
    required_files = [
        'sync.py',
        'sync_executable.py',
        'config.py',
        'etl/__init__.py',
        'etl/sync.py',
        'etl/extract.py',
        'etl/transform.py',
        'etl/load.py',
        'etl/utils.py',
    ]
    
    required_directories = [
        'etl',
        'logs',
        'output',
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.isfile(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {', '.join(missing_files)}")
        return False
    
    missing_directories = []
    for directory in required_directories:
        if not os.path.isdir(directory):
            missing_directories.append(directory)
    
    if missing_directories:
        logger.error(f"Missing required directories: {', '.join(missing_directories)}")
        logger.info("Creating missing directories...")
        for directory in missing_directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    logger.info("Project structure is valid")
    return True

def check_packaging_tools():
    """Check if packaging script and spec files exist."""
    packaging_tools = [
        'build_executable.py',
        'generate_spec.py',
        'generate_icon.py',
    ]
    
    missing_tools = []
    for tool in packaging_tools:
        if not os.path.isfile(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        logger.warning(f"Missing packaging tools: {', '.join(missing_tools)}")
        return False
    
    logger.info("All packaging tools are present")
    return True

def check_icon():
    """Check if icon file exists or can be generated."""
    icon_path = 'generated-icon.png'
    
    if os.path.isfile(icon_path):
        logger.info(f"Icon file exists: {icon_path}")
        return True
    
    logger.warning(f"Icon file not found: {icon_path}")
    
    if os.path.isfile('generate_icon.py'):
        logger.info("Attempting to generate icon...")
        try:
            result = subprocess.run([sys.executable, 'generate_icon.py'], 
                                    capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.isfile(icon_path):
                logger.info("Icon generated successfully")
                return True
            else:
                logger.warning("Failed to generate icon")
                return False
        except Exception as e:
            logger.warning(f"Error generating icon: {e}")
            return False
    
    logger.warning("Icon generator not found, icon will not be included in package")
    return False

def check_documentation():
    """Check if documentation files exist."""
    documentation_files = [
        'README.md',
        'INSTALLATION.md',
        'PACKAGING.md',
    ]
    
    missing_docs = []
    for doc in documentation_files:
        if not os.path.isfile(doc):
            missing_docs.append(doc)
    
    if missing_docs:
        logger.warning(f"Missing documentation files: {', '.join(missing_docs)}")
        return False
    
    logger.info("All documentation files are present")
    return True

def main():
    """Main entry point."""
    logger.info("=== Checking System Readiness for Packaging CountyDataSync ===")
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check PyInstaller
    pyinstaller_ok = check_pyinstaller()
    
    # Check dependencies
    dependencies_ok = check_dependencies()
    
    # Check project structure
    structure_ok = check_project_structure()
    
    # Check packaging tools
    tools_ok = check_packaging_tools()
    
    # Check icon
    icon_ok = check_icon()
    
    # Check documentation
    docs_ok = check_documentation()
    
    # Print summary
    print("\n=== Readiness Summary ===")
    print(f"Python Version: {'✓' if python_ok else '✗'}")
    print(f"PyInstaller: {'✓' if pyinstaller_ok else '✗'}")
    print(f"Dependencies: {'✓' if dependencies_ok else '✗'}")
    print(f"Project Structure: {'✓' if structure_ok else '✗'}")
    print(f"Packaging Tools: {'✓' if tools_ok else '✗'}")
    print(f"Icon: {'✓' if icon_ok else '⚠'}")
    print(f"Documentation: {'✓' if docs_ok else '⚠'}")
    
    # Overall status
    required_checks = [python_ok, pyinstaller_ok, dependencies_ok, structure_ok]
    if all(required_checks):
        logger.info("System is ready for packaging!")
        return 0
    else:
        logger.error("System is not ready for packaging. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())