"""Windows-specific runtime helpers."""

from __future__ import annotations

import subprocess
import sys

__all__ = ["hidden_subprocess_kwargs", "is_admin"]


def is_admin() -> bool:
    """Return True when the current process has administrator privileges."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def hidden_subprocess_kwargs() -> dict:
    """Return subprocess kwargs that hide the console window on Windows."""
    if sys.platform != "win32":
        return {}

    kwargs: dict = {}
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    kwargs["creationflags"] = creationflags

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    kwargs["startupinfo"] = startupinfo
    return kwargs
