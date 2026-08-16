"""Typed exceptions for LibreHardwareMonitor integration."""


class LhmDllNotFoundError(Exception):
    """Raised when LibreHardwareMonitorLib.dll is missing from vendor directory."""


class LhmRuntimeError(Exception):
    """Raised when CLR/DLL load fails at runtime."""
