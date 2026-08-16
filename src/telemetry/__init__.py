"""Telemetry layer — LibreHardwareMonitor sensor polling."""

from src.telemetry.exceptions import LhmDllNotFoundError, LhmRuntimeError
from src.telemetry.lhm_wrapper import LhmBackend, LhmBridge, SensorReading, default_vendor_dir
from src.telemetry.sensor_reader import TelemetryPoller, compute_peak, main

__all__ = [
    "LhmBackend",
    "LhmBridge",
    "LhmDllNotFoundError",
    "LhmRuntimeError",
    "SensorReading",
    "TelemetryPoller",
    "compute_peak",
    "default_vendor_dir",
    "main",
]
