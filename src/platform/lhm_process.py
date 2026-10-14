"""Detect conflicts with other LibreHardwareMonitor processes."""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

__all__ = ["is_lhm_gui_running", "warn_if_lhm_gui_running"]


def is_lhm_gui_running() -> bool:
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq LibreHardwareMonitor.exe", "/NH"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return False
    return "LibreHardwareMonitor.exe" in result.stdout


def warn_if_lhm_gui_running() -> None:
    if is_lhm_gui_running():
        logger.warning(
            "LibreHardwareMonitor.exe is also running — both apps access CPU MSR "
            "sensors and readings may disagree. Close the official app for consistent values."
        )
