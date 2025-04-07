#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check packaging readiness for CountyDataSync

This script verifies that all required packages and tools are installed
for packaging CountyDataSync as a standalone executable.

Usage:
    python check_packaging_readiness.py
"""

import sys
import importlib
import subprocess
import platform
import os
import shutil

# Required Python packages
REQUIRED_PACKAGES = [
    'pandas',
    'numpy',
    'geopandas',
    'pyodbc',
    'sqlalchemy',
    'shapely',
    'psutil',
    'python-dotenv',
    'flask',
    'pyinstaller'
]

# Required files for packaging
REQUIRED_FILES = [
    'main.py',
    'build_executable.py',
    'package_application.py'
]

def check_python_version():
    """Check if Python version is adequate."""
    print("\nChecking Python version:")
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print(f"❌ Python 3.7+ is required. Current version: {sys.version}")
        return False
    else:
        print(f"✓ Python version is adequate: {sys.version}")
        return True

def check_packages():
    """Check if all required packages are installed."""
    print("\nChecking required packages:")
    all_installed = True
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
            all_installed = False
    
    if not all_installed:
        print("\nInstall missing packages with:")
        print(f"  pip install {' '.join(missing_packages)}")
    
    return all_installed

def check_pyinstaller():
    """Check if PyInstaller is working properly."""
    print("\nTesting PyInstaller:")
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                               capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"✓ PyInstaller version: {version}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ PyInstaller is not working properly")
        return False

def check_files():
    """Check if required files for packaging exist."""
    print("\nChecking required files:")
    all_exist = True
    
    for file in REQUIRED_FILES:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"❌ {file} is missing")
            all_exist = False
    
    return all_exist

def check_installer_tools():
    """Check if installer creation tools are available."""
    print("\nChecking installer tools:")
    sys_platform = platform.system()
    
    if sys_platform == 'Windows':
        nsis_path = shutil.which('makensis')
        if nsis_path:
            print(f"✓ NSIS found: {nsis_path}")
            return True
        else:
            print("ℹ️ NSIS not found. Install from https://nsis.sourceforge.io/ to create Windows installers")
            return False
    
    elif sys_platform == 'Darwin':  # macOS
        create_dmg_path = shutil.which('create-dmg')
        if create_dmg_path:
            print(f"✓ create-dmg found: {create_dmg_path}")
            return True
        else:
            print("ℹ️ create-dmg not found. Install with 'brew install create-dmg' to create macOS installers")
            return False
    
    else:  # Linux
        print("ℹ️ No specific installer tool check for Linux")
        return True

def check_azure_tools():
    """Check if Azure deployment tools are available."""
    print("\nChecking Azure tools:")
    
    az_cli_path = shutil.which('az')
    if az_cli_path:
        try:
            # Get Azure CLI version
            result = subprocess.run(['az', '--version'], 
                                   capture_output=True, text=True, check=True)
            print(f"✓ Azure CLI is installed")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("❌ Azure CLI is installed but not working properly")
            return False
    else:
        print("ℹ️ Azure CLI not found. Install it to deploy to Azure")
        return False

def main():
    """Main function to check packaging readiness."""
    print("=" * 60)
    print("CountyDataSync Packaging Readiness Check")
    print("=" * 60)
    
    checks = [
        ("Python version", check_python_version()),
        ("Required packages", check_packages()),
        ("PyInstaller", check_pyinstaller()),
        ("Required files", check_files()),
        ("Installer tools", check_installer_tools()),
        ("Azure tools", check_azure_tools())
    ]
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    all_required_ok = True
    
    for name, result in checks:
        if name in ["Python version", "Required packages", "PyInstaller", "Required files"]:
            if not result:
                all_required_ok = False
            status = "✓" if result else "❌"
        else:
            status = "✓" if result else "ℹ️"
            
        print(f"{status} {name}")
    
    print("\nVerdict:", end=" ")
    if all_required_ok:
        print("✅ Ready for packaging! All required components are available.")
        return 0
    else:
        print("❌ Not ready for packaging. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())