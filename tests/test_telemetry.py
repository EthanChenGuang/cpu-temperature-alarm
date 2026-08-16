"""WSL-safe unit tests for telemetry peak logic and poller behavior."""

from src.telemetry.lhm_wrapper import SensorReading
from src.telemetry.sensor_reader import compute_peak


def test_compute_peak_returns_max_of_valid_readings():
    readings = [
        SensorReading(name="CPU / Package", value_celsius=65.0),
        SensorReading(name="GPU / Core", value_celsius=72.0),
    ]
    assert compute_peak(readings) == 72.0
