# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync_executable.py'],
    pathex=['/home/runner/workspace'],
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
    hooksconfig={},
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
    icon='/home/runner/workspace/generated-icon.png',
)
