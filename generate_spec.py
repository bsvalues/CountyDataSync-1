#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate a PyInstaller spec file for packaging CountyDataSync.
"""

import os
import sys
from pathlib import Path


def generate_spec_file():
    """Generate a PyInstaller spec file."""
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Please install it with 'pip install pyinstaller'.")
        sys.exit(1)
    
    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "generated-icon.png")
    
    # Ensure icon exists
    if not os.path.exists(icon_path):
        try:
            from generate_icon import generate_icon
            generate_icon()
            print(f"Generated icon at {icon_path}")
        except ImportError:
            print("Warning: Could not generate icon. Icon will not be included in the executable.")
            icon_path = None

    # Define the spec file content
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync_executable.py'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[
        ('.env.example', '.'),
        ('README.md', '.'),
        ('INSTALLATION.md', '.'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'sqlalchemy',
        'pyodbc',
        'psutil',
        'dotenv',
        'flask',
        'werkzeug',
        'geopandas',
        'shapely',
        'etl',
        'etl.extract',
        'etl.transform',
        'etl.load',
        'etl.sync',
        'etl.data_quality',
        'etl.data_validation',
        'etl.delta_sync',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CountyDataSync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {'icon=' + repr(icon_path) + ',' if icon_path else ''}
)
"""

    # Write the spec file
    spec_file = os.path.join(current_dir, "countydatasync.spec")
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    print(f"Generated spec file at {spec_file}")
    return spec_file


if __name__ == "__main__":
    generate_spec_file()