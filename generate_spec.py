#!/usr/bin/env python3
"""
Generate a PyInstaller spec file for packaging CountyDataSync.
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_spec_file():
    """Generate a PyInstaller spec file."""
    logger.info("Generating PyInstaller spec file")
    
    # Check if icon exists
    icon_path = 'generated-icon.png'
    if not os.path.exists(icon_path):
        logger.warning(f"Icon file {icon_path} not found. Trying to generate it.")
        try:
            import generate_icon
            icon_path = generate_icon.generate_icon()
            if not icon_path:
                logger.warning("Failed to generate icon. Spec file will not include an icon.")
                icon_path = None
        except ImportError:
            logger.warning("Could not import generate_icon module. Spec file will not include an icon.")
            icon_path = None
    
    # Determine platform-specific file extension
    if sys.platform.startswith('win'):
        extension = '.exe'
    elif sys.platform.startswith('darwin'):
        extension = '.app'
    else:
        extension = ''
    
    # Create the spec file content
    icon_line = f"icon='{icon_path}'," if icon_path else ""
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('etl', 'etl'),
        ('config.py', '.'),
        ('README.md', '.'),
        ('logs', 'logs'),
        ('output', 'output'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'pyodbc',
        'geopandas',
        'shapely',
        'sqlite3',
        'dotenv',
        'psutil',
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

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

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
    {icon_line}
)
"""
    
    # Write the spec file
    spec_file = 'countydatasync.spec'
    try:
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        logger.info(f"Spec file generated successfully: {spec_file}")
        return os.path.abspath(spec_file)
    except Exception as e:
        logger.error(f"Error writing spec file: {e}")
        return None

if __name__ == "__main__":
    # Generate the spec file
    spec_path = generate_spec_file()
    
    if spec_path:
        print(f"PyInstaller spec file generated successfully: {spec_path}")
        sys.exit(0)
    else:
        print("Failed to generate PyInstaller spec file")
        sys.exit(1)