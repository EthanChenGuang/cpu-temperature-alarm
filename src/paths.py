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
    return app_root() / "vendor" / "LibreHardwareMonitor"


def config_dir() -> Path:
    return app_root() / "config"
