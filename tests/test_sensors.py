"""Tests for LHM sensor name filtering."""

from src.telemetry.sensors import is_absolute_temperature_sensor


def test_is_absolute_temperature_sensor_rejects_distance_to_tjmax():
    assert is_absolute_temperature_sensor("P-Core #1 Distance to TjMax") is False
    assert is_absolute_temperature_sensor("E-Core #3 Distance to TjMax") is False


def test_is_absolute_temperature_sensor_accepts_real_temps():
    assert is_absolute_temperature_sensor("CPU Package") is True
    assert is_absolute_temperature_sensor("Core Max") is True
    assert is_absolute_temperature_sensor("GPU Hot Spot") is True
