# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for CPU High Temperature Alert.

Set PYI_ONEFILE=1 for a single portable exe (default).
Set PYI_ONEFILE=0 for one-folder COLLECT output (fallback if DLL loading fails).
"""

import os
from pathlib import Path

block_cipher = None
one_file = os.environ.get("PYI_ONEFILE", "1") != "0"
repo_root = Path(SPECPATH)
icon_path = repo_root / "assets" / "cpu-temp-alert.ico"
exe_icon = str(icon_path) if icon_path.is_file() else None

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
        "certifi",
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
    runtime_hooks=[str(repo_root / "scripts" / "pyi_rth_ssl.py")],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if one_file:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="cpu-temp-alert",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        uac_admin=True,
        icon=exe_icon,
    )
else:
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
        uac_admin=True,
        icon=exe_icon,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="cpu-temp-alert",
    )
