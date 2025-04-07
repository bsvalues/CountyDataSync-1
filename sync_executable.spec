# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync.py'],  # Main script
    pathex=[],
    binaries=[],
    datas=[
        ('etl', 'etl'),  # Include the etl package
        ('.env.example', '.'),  # Include the example env file
    ],
    hiddenimports=[
        'etl',
        'etl.extract',
        'etl.transform',
        'etl.load',
        'etl.sync',
        'etl.utils',
        'etl.test_data',
        'pandas',
        'geopandas',
        'shapely',
        'numpy',
        'pyodbc',
        'sqlalchemy',
        'dotenv',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
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
    icon='generated-icon.png',
)
