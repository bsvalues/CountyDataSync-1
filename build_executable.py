#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build script for creating a standalone executable of CountyDataSync using PyInstaller.

Usage:
    python build_executable.py
"""

import os
import subprocess
import sys
import platform


def check_prerequisites():
    """Check if all prerequisites are installed."""
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("Error: Python 3.7 or higher is required.")
        return False
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("Error: PyInstaller is not installed. Install it with 'pip install pyinstaller'.")
        return False
    
    # Since we've installed all required packages and verified it with
    # check_packaging_readiness.py, we can skip detailed package checks here
    print("All prerequisites are met.")
    return True


def generate_spec_file():
    """Generate or update the PyInstaller spec file."""
    spec_file = "countydatasync.spec"
    if not os.path.exists(spec_file):
        try:
            from generate_spec import generate_spec_file
            spec_file = generate_spec_file()
            print(f"Generated spec file: {spec_file}")
        except ImportError:
            print("Error: generate_spec.py not found or has errors.")
            return None
    else:
        print(f"Using existing spec file: {spec_file}")
    
    return spec_file


def build_executable():
    """Build the executable using PyInstaller."""
    if not check_prerequisites():
        return False
    
    # Generate spec file if needed
    spec_file = generate_spec_file()
    if not spec_file:
        return False
    
    # Build with PyInstaller
    print("Building executable with PyInstaller...")
    cmd = ['pyinstaller', '--clean', '--noconfirm', spec_file]
    
    try:
        result = subprocess.run(cmd, check=True, text=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout)
        
        # Check if build was successful
        if os.path.exists(os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))):
            print("Build successful! Executable created in 'dist' directory.")
            return True
        else:
            print("Build failed: Executable not found in 'dist' directory.")
            print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Build failed with error: {str(e)}")
        return False


def main():
    """Run the PyInstaller build process."""
    print("=" * 60)
    print("CountyDataSync PyInstaller Build Script")
    print("=" * 60)
    
    if build_executable():
        print("\nBuild completed successfully!")
        exe_path = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
        print(f"Executable path: {os.path.abspath(exe_path)}")
        
        # Suggest next steps
        print("\nNext steps:")
        print("1. Test the executable: python test_packaged_executable.py")
        print("2. Create a distribution package: python package_application.py --version X.Y.Z")
    else:
        print("\nBuild failed. Please fix the errors and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()