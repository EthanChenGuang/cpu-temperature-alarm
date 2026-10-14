"""Helpers for interpreting LibreHardwareMonitor temperature sensor names."""

from __future__ import annotations

__all__ = ["is_absolute_temperature_sensor"]


def is_absolute_temperature_sensor(sensor_name: str) -> bool:
    """Return False for derived Intel metrics that LHM exposes as Temperature type."""
    lowered = sensor_name.lower()
    if "distance to tjmax" in lowered:
        return False
    return True
