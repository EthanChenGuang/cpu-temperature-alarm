# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for CPU High Temperature Alert — one-folder Windows build."""

from pathlib import Path

block_cipher = None
repo_root = Path(SPECPATH)

a = Analysis(
    [str(repo_root / "src" / "main.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[
        (
            str(repo_root / "vendor" / "LibreHardwareMonitor"),
            "vendor/LibreHardwareMonitor",
        ),
    ],
    hiddenimports=[
        "clr",
        "pystray",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "requests",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
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
    [],
    exclude_binaries=True,
    name="cpu-temp-alert",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="cpu-temp-alert",
)
