"""Ensure only one tray instance runs at a time."""

from __future__ import annotations

import ctypes
import logging
import sys

logger = logging.getLogger(__name__)

_MUTEX_NAME = "Global\\CpuTempAlertSingleton_v1"
_ERROR_ALREADY_EXISTS = 183


def acquire_single_instance() -> bool:
    """Return False when another tray instance is already running."""
    if sys.platform != "win32":
        return True

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    if not handle:
        logger.error("Could not create single-instance mutex — continuing anyway")
        return True

    last_error = kernel32.GetLastError()
    if last_error == _ERROR_ALREADY_EXISTS:
        logger.error(
            "Another CPU Temp Alert instance is already running. "
            "Exit the existing tray icon before starting a new copy."
        )
        return False
    return True
