"""Application root paths — dev source tree vs PyInstaller frozen bundle."""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["app_root", "config_dir", "vendor_dir"]


def app_root() -> Path:
    """Return install directory (frozen exe folder) or repository root in dev."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def vendor_dir() -> Path:
    root = app_root()
    candidates: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "vendor" / "LibreHardwareMonitor")
    candidates.extend(
        (
            root / "vendor" / "LibreHardwareMonitor",
            root / "_internal" / "vendor" / "LibreHardwareMonitor",
        )
    )
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def config_dir() -> Path:
    return app_root() / "config"
