# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync_executable.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('etl', 'etl'),
        ('config.py', '.'),
        ('README.md', '.'),
        ('logs', 'logs'),
        ('output', 'output'),
        ('.env.example', '.'),
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
        'etl.sync',
        'etl.extract',
        'etl.transform',
        'etl.load',
        'etl.utils',
        'etl.data_quality',
        'etl.data_validation',
        'etl.integrate_quality_heatmap',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'flask',  # Exclude web components for the standalone executable
        'flask_sqlalchemy',
        'werkzeug',
    ],
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