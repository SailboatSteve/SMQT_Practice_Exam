# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct

block_cipher = None

added_files = [
    ('templates', 'templates'),  # All template files including new help.html, goodbye.html, etc.
    ('regulations.json', '.'),
    ('test_questions.json', '.'),  # Initial question pool
    ('.env.template', '.'),  # Environment variables template
    ('static', 'static'),  # Static assets including favicon
    ('README.md', '.')  # Documentation
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask',
        'flask_wtf',
        'requests',
        'datetime',
        'glob',
        'json',
        'werkzeug.security',
        'os.path',
        'random',
        'base64',
        'dotenv'
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

# Add version info
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 2, 0, 0),  # Updated version for backup and sharing features
        prodvers=(1, 2, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('CompanyName', 'SMQT Practice Test'),
                    StringStruct('FileDescription', 'SMQT Practice Test Application'),
                    StringStruct('FileVersion', '1.2.0'),
                    StringStruct('InternalName', 'SMQT_Practice'),
                    StringStruct('LegalCopyright', ' 2025'),
                    StringStruct('OriginalFilename', 'SMQT_Practice.exe'),
                    StringStruct('ProductName', 'SMQT Practice Test'),
                    StringStruct('ProductVersion', '1.2.0')
                ])
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SMQT_Practice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_info  # Add version info
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SMQT_Practice')
