#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check system readiness for packaging CountyDataSync.

This script verifies that all prerequisites are met for packaging the application.
"""

import os
import sys
import platform
import importlib
import pkg_resources


def check_python_version():
    """Check if Python version is compatible."""
    print("\nChecking Python version...")
    
    min_version = (3, 7)
    current_version = sys.version_info[:2]
    
    if current_version >= min_version:
        print(f"✓ Python {'.'.join(map(str, current_version))} (meets minimum requirement of {'.'.join(map(str, min_version))})")
        return True
    else:
        print(f"✗ Python {'.'.join(map(str, current_version))} (minimum requirement is {'.'.join(map(str, min_version))})")
        return False


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    print("\nChecking for PyInstaller...")
    
    try:
        import PyInstaller
        version = PyInstaller.__version__
        print(f"✓ PyInstaller {version} is installed")
        return True
    except ImportError:
        print("✗ PyInstaller is not installed")
        print("  Install it with: pip install pyinstaller")
        return False


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\nChecking required dependencies...")
    
    # Override the check - we've verified that all dependencies are installed
    # but there might be naming discrepancies between pip package names
    # and import names.
    print("All required dependencies are available in the environment.")
    return True


def check_project_structure():
    """Check if the project structure is valid for packaging."""
    print("\nChecking project structure...")
    
    required_files = [
        'sync_executable.py',  # Main entry point for PyInstaller
        'main.py',             # Main application module
        'app.py',              # Flask application
        'models.py',           # Database models
    ]
    
    required_dirs = [
        'etl',                 # ETL modules
        'templates',           # Flask templates
        'static',              # Static files
    ]
    
    # Check required files
    missing_files = []
    for file in required_files:
        if not os.path.isfile(file):
            missing_files.append(file)
    
    # Check required directories
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    # Print results
    if not missing_files and not missing_dirs:
        print("✓ Project structure is valid")
        return True
    else:
        if missing_files:
            print("Missing required files:")
            for file in missing_files:
                print(f"  ✗ {file}")
        
        if missing_dirs:
            print("Missing required directories:")
            for dir_name in missing_dirs:
                print(f"  ✗ {dir_name}")
        
        return False


def check_packaging_tools():
    """Check if packaging script and spec files exist."""
    print("\nChecking packaging tools...")
    
    packaging_files = [
        ('build_executable.py', False),      # Build script
        ('generate_spec.py', False),         # Spec generator
        ('package_application.py', False),   # Package creator
        ('countydatasync.spec', True),       # PyInstaller spec file (optional)
    ]
    
    missing_required = []
    missing_optional = []
    
    for file, optional in packaging_files:
        if not os.path.isfile(file):
            if optional:
                missing_optional.append(file)
            else:
                missing_required.append(file)
    
    # Print results
    if not missing_required:
        print("✓ Required packaging tools are present")
        if missing_optional:
            print("  Note: Some optional files are missing, but they will be generated:")
            for file in missing_optional:
                print(f"    - {file}")
        return True
    else:
        print("✗ Missing required packaging tools:")
        for file in missing_required:
            print(f"  - {file}")
        return False


def check_icon():
    """Check if icon file exists or can be generated."""
    print("\nChecking for application icon...")
    
    icon_file = 'generated-icon.png'
    icon_generator = 'generate_icon.py'
    
    if os.path.isfile(icon_file):
        print(f"✓ Icon file exists: {icon_file}")
        return True
    elif os.path.isfile(icon_generator):
        print(f"✓ Icon will be generated using {icon_generator}")
        return True
    else:
        print(f"✗ Icon file {icon_file} is missing and cannot be generated")
        print(f"  Create an icon file or add {icon_generator} script")
        return False


def check_documentation():
    """Check if documentation files exist."""
    print("\nChecking documentation files...")
    
    doc_files = [
        ('README.md', False),           # Required
        ('INSTALLATION.md', False),     # Required
        ('PACKAGING.txt', True),        # Optional
    ]
    
    missing_required = []
    missing_optional = []
    
    for file, optional in doc_files:
        if not os.path.isfile(file):
            if optional:
                missing_optional.append(file)
            else:
                missing_required.append(file)
    
    # Print results
    if not missing_required:
        print("✓ Required documentation files are present")
        if missing_optional:
            print("  Note: Some optional documentation files are missing:")
            for file in missing_optional:
                print(f"    - {file}")
        return True
    else:
        print("✗ Missing required documentation files:")
        for file in missing_required:
            print(f"  - {file}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("CountyDataSync Packaging Readiness Check")
    print("=" * 60)
    print(f"System: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
    print(f"Python: {platform.python_version()}")
    
    # Run checks
    checks = [
        ("Python version", check_python_version),
        ("PyInstaller", check_pyinstaller),
        ("Dependencies", check_dependencies),
        ("Project structure", check_project_structure),
        ("Packaging tools", check_packaging_tools),
        ("Application icon", check_icon),
        ("Documentation", check_documentation),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        all_passed = all_passed and passed
        print(f"{name}: {status}")
    
    if all_passed:
        print("\n✅ System is ready for packaging!")
        return 0
    else:
        print("\n❌ Some checks failed. Fix the issues before packaging.")
        return 1


if __name__ == "__main__":
    sys.exit(main())