"""
Build script for creating a standalone executable of CountyDataSync using PyInstaller.

Usage:
    python build_executable.py
"""
import os
import subprocess
import sys
import time

def main():
    """Run the PyInstaller build process."""
    print("Starting CountyDataSync executable build...")
    
    # First, generate the spec file if it doesn't exist
    if not os.path.exists('sync_executable.spec'):
        print("Generating spec file...")
        try:
            from generate_spec import generate_spec_file
            generate_spec_file()
        except Exception as e:
            print(f"Error generating spec file: {str(e)}")
            sys.exit(1)
    
    # Run PyInstaller
    print("Running PyInstaller...")
    start_time = time.time()
    try:
        subprocess.run(
            ["pyinstaller", "--clean", "sync_executable.spec"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with error code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running PyInstaller: {str(e)}")
        sys.exit(1)
    
    build_time = time.time() - start_time
    print(f"Build completed in {build_time:.2f} seconds")
    
    # Check if the executable was created
    executable_path = os.path.join('dist', 'CountyDataSync')
    if os.path.exists(executable_path):
        print(f"Executable created at: {executable_path}")
        
        # Get file size
        size_bytes = os.path.getsize(executable_path)
        size_mb = size_bytes / (1024 * 1024)
        print(f"Executable size: {size_mb:.2f} MB")
        
        print("\nYou can now run the executable with:")
        print(f"./dist/CountyDataSync")
    else:
        print("Executable not found. Build may have failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()