#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package CountyDataSync for distribution.

This script creates a complete distribution package with the standalone executable,
configuration files, and documentation.

Usage:
    python package_application.py [--version VERSION]

Arguments:
    --version VERSION: Version string to use for the package (default: current date)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
import zipfile


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Package CountyDataSync for distribution')
    
    # Version argument with default to current date
    default_version = datetime.now().strftime('%Y%m%d')
    parser.add_argument('--version', type=str, default=default_version,
                       help='Version string for the package (default: current date)')
    
    return parser.parse_args()


def build_executable():
    """Build the executable using build_executable.py."""
    print("Building executable...")
    
    try:
        # Check if build_executable.py exists
        if not os.path.exists('build_executable.py'):
            print("Error: build_executable.py not found.")
            return False
        
        # Run the build script
        result = subprocess.run([sys.executable, 'build_executable.py'],
                               check=True, capture_output=True, text=True)
        
        # Check for successful build
        exe_path = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
        if os.path.exists(exe_path):
            print("Executable built successfully!")
            return True
        else:
            print("Failed to build executable.")
            print(result.stdout)
            print(result.stderr)
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Build failed with error: {str(e)}")
        return False


def copy_documentation(dist_dir):
    """Copy documentation files to distribution directory."""
    print("Copying documentation...")
    
    # List of documentation files to copy
    doc_files = [
        'README.md',
        'INSTALLATION.md',
        'PACKAGING.txt',
    ]
    
    # Copy each file if it exists
    for file in doc_files:
        if os.path.exists(file):
            shutil.copy2(file, dist_dir)
            print(f"Copied {file}")
        else:
            print(f"Warning: {file} not found, skipping.")


def copy_config_files(dist_dir):
    """Copy configuration files to distribution directory."""
    print("Copying configuration files...")
    
    # Copy .env.example if it exists
    if os.path.exists('.env.example'):
        shutil.copy2('.env.example', os.path.join(dist_dir, '.env.example'))
        print("Copied .env.example")
    else:
        # Create a basic .env.example file
        with open(os.path.join(dist_dir, '.env.example'), 'w') as f:
            f.write("# CountyDataSync Environment Configuration\n\n")
            f.write("# Database connection (PostgreSQL or SQLite)\n")
            f.write("DATABASE_URL=sqlite:///instance/countydatasync.db\n\n")
            f.write("# SQL Server connection (for data extraction)\n")
            f.write("MSSQL_SERVER=your_server_address\n")
            f.write("MSSQL_DATABASE=your_database_name\n")
            f.write("MSSQL_USERNAME=your_username\n")
            f.write("MSSQL_PASSWORD=your_password\n\n")
            f.write("# Set to 'true' to use test data instead of SQL Server\n")
            f.write("USE_TEST_DATA=false\n")
        print("Created .env.example")
    
    # Copy config.py if it exists
    if os.path.exists('config.py'):
        shutil.copy2('config.py', dist_dir)
        print("Copied config.py")


def create_directory_structure(dist_dir):
    """Create necessary directories in the distribution package."""
    print("Creating directory structure...")
    
    # Create directories
    for directory in ['logs', 'output', 'data']:
        os.makedirs(os.path.join(dist_dir, directory), exist_ok=True)
        print(f"Created {directory} directory")
    
    # Create a .keep file in each directory
    for directory in ['logs', 'output', 'data']:
        with open(os.path.join(dist_dir, directory, '.keep'), 'w') as f:
            f.write("# This file ensures the directory is included in the package\n")


def create_distribution_package(version):
    """Create distribution package."""
    print("\nCreating distribution package...")
    
    # Define paths
    exe_name = 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else '')
    exe_path = os.path.join('dist', exe_name)
    dist_dir = f'CountyDataSync-{version}'
    
    # Check if executable exists
    if not os.path.exists(exe_path):
        print(f"Error: Executable not found at {exe_path}")
        return False
    
    # Create distribution directory
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy executable
    shutil.copy2(exe_path, os.path.join(dist_dir, exe_name))
    print(f"Copied executable to {dist_dir}")
    
    # Create directory structure
    create_directory_structure(dist_dir)
    
    # Copy documentation
    copy_documentation(dist_dir)
    
    # Copy configuration files
    copy_config_files(dist_dir)
    
    # Create zip archive
    zip_filename = f'{dist_dir}.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(dist_dir)))
    
    print(f"\nDistribution package created: {zip_filename}")
    return True


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    print("=" * 60)
    print(f"CountyDataSync Packaging (Version: {args.version})")
    print("=" * 60)
    
    # Build executable if it doesn't exist
    exe_path = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
    if not os.path.exists(exe_path):
        if not build_executable():
            print("Aborting package creation due to build failures.")
            sys.exit(1)
    else:
        print(f"Using existing executable at {exe_path}")
    
    # Create distribution package
    if create_distribution_package(args.version):
        print("\nPackaging completed successfully!")
    else:
        print("\nPackaging failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()