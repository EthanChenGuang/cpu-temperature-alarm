"""WSL-safe unit tests for telemetry peak logic and poller behavior."""

import logging

import pytest

from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import SensorReading
from src.telemetry.sensor_reader import TelemetryPoller, compute_peak, read_sensors


def test_compute_peak_returns_max_of_valid_readings():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=65.0),
        SensorReading(name="GPU / Core", value_celsius=72.0),
    ]
    assert compute_peak(readings) == 72.0


def test_compute_peak_skips_invalid_range():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=72.0),
        SensorReading(name="GPU / Core", value_celsius=999.0),
    ]
    assert compute_peak(readings) == 72.0


def test_compute_peak_returns_none_when_all_invalid():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=0.0),
        SensorReading(name="GPU / Core", value_celsius=200.0),
    ]
    assert compute_peak(readings) is None


def test_compute_peak_warns_once_per_sensor(caplog):
    warned: set[str] = set()
    readings = [
        SensorReading(name="CPU / Package", value_celsius=-1.0),
        SensorReading(name="CPU / Package", value_celsius=-1.0),
    ]
    with caplog.at_level(logging.WARNING):
        assert compute_peak(readings, warned) is None
        assert sum("CPU / Package" in r.message for r in caplog.records) == 1

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert compute_peak(readings, warned) is None
        assert len(caplog.records) == 0

    valid = [SensorReading(name="CPU / Package", value_celsius=55.0)]
    with caplog.at_level(logging.WARNING):
        assert compute_peak(valid, warned) == 55.0

    caplog.clear()
    invalid_again = [SensorReading(name="CPU / Package", value_celsius=-1.0)]
    with caplog.at_level(logging.WARNING):
        assert compute_peak(invalid_again, warned) is None
        assert len(caplog.records) == 1


def test_compute_peak_max_across_multiple_gpus():
    readings = [
        SensorReading(name="GPU / Core", value_celsius=60.0),
        SensorReading(name="GPU / Hot Spot", value_celsius=78.0),
    ]
    assert compute_peak(readings) == 78.0


def test_compute_peak_max_across_cpu_sockets():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=55.0),
        SensorReading(name="CPU / CCD #1", value_celsius=68.0),
    ]
    assert compute_peak(readings) == 68.0


def test_compute_peak_includes_auxiliary_sensors():
    readings = [
        SensorReading(name="GPU / Hot Spot", value_celsius=82.0),
        SensorReading(name="GPU / Memory", value_celsius=70.0),
    ]
    assert compute_peak(readings) == 82.0


def test_compute_peak_partial_valid_sensors():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=0.0),
        SensorReading(name="GPU / Core", value_celsius=63.0),
    ]
    assert compute_peak(readings) == 63.0


def test_compute_peak_recomputes_independently_each_cycle():
    warned: set[str] = set()
    first = [SensorReading(name="CPU / Package", value_celsius=50.0)]
    second = [SensorReading(name="CPU / Package", value_celsius=90.0)]
    assert compute_peak(first, warned) == 50.0
    assert compute_peak(second, warned) == 90.0


class FakeLhmBackend:
    def __init__(self, readings: list[SensorReading]) -> None:
        self._readings = readings

    def read_temperatures(self) -> list[SensorReading]:
        return list(self._readings)


def test_read_sensors_returns_readings_and_peak():
    backend = FakeLhmBackend(
        [
            SensorReading(name="CPU / Package", value_celsius=45.0),
            SensorReading(name="GPU / Core", value_celsius=55.0),
        ]
    )
    result = read_sensors(backend)
    assert result.peak_temp == 55.0
    assert len(result.readings) == 2


def test_telemetry_poller_run_once():
    backend = FakeLhmBackend([SensorReading(name="CPU / Package", value_celsius=42.0)])
    poller = TelemetryPoller(backend)
    readings, peak = poller.run_once()
    assert len(readings) == 1
    assert peak == 42.0


def test_telemetry_poller_empty_sensors_yields_none_peak():
    backend = FakeLhmBackend([])
    poller = TelemetryPoller(backend)
    _, peak = poller.run_once()
    assert peak is None
