# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Nutrition Label Generator Demo.

Build with: pyinstaller nutrition_label.spec --clean

Note: PyInstaller must be run on Windows to create a Windows executable.
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hidden imports for the dependencies
hiddenimports = [
    # Uvicorn
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',

    # FastAPI / Starlette
    'fastapi',
    'starlette',
    'starlette.applications',
    'starlette.responses',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.middleware.errors',
    'starlette.middleware.gzip',
    'starlette.staticfiles',
    'starlette.templating',
    'starlette.status',

    # Pydantic
    'pydantic',
    'pydantic_settings',
    'pydantic.deprecated.decorator',
    'pydantic._internal._config',
    'pydantic._internal._generate_schema',
    'pydantic._internal._validators',
    'pydantic_core',

    # Database
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.declarative',

    # HTTP clients
    'httpx',
    'httpcore',
    'h11',
    'anyio',
    'anyio._backends._asyncio',
    'sniffio',
    'certifi',

    # OpenAI
    'openai',
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',

    # Image processing
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',

    # PDF processing
    'fitz',  # PyMuPDF
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.platypus',

    # Rate limiting
    'slowapi',
    'slowapi.errors',
    'slowapi.util',
    'slowapi.extension',

    # Other dependencies
    'dotenv',
    'email_validator',
    'multipart',
    'python_multipart',
]

# Collect data files
datas = [
    # Backend source code
    ('backend', 'backend'),
    # Frontend static files (already in backend/static)
]

# Check if .env exists and include it
if os.path.exists('.env'):
    datas.append(('.env', '.'))

# Analysis
a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary large packages
        'matplotlib',
        'scipy',
        'numpy.testing',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NutritionLabelGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console window - closing it stops the server
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NutritionLabelGenerator',
)
