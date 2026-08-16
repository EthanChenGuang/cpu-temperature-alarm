"""Telemetry sensor polling and peak temperature computation."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone

from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBackend, LhmBridge, SensorReading

__all__ = ["SensorReading", "compute_peak", "TelemetryPoller", "main"]

MIN_VALID_C = 0
MAX_VALID_C = 150


def compute_peak(
    readings: list[SensorReading],
    warned_sensors: set[str] | None = None,
) -> float | None:
    """Return max valid temperature or None if no valid readings."""
    valid: list[float] = []
    for reading in readings:
        if reading.value_celsius <= MIN_VALID_C or reading.value_celsius > MAX_VALID_C:
            continue
        valid.append(reading.value_celsius)
    return max(valid) if valid else None


class TelemetryPoller:
    def __init__(self, backend: LhmBackend, poll_interval_seconds: float = 3) -> None:
        self._backend = backend
        self._poll_interval = poll_interval_seconds
        self._warned_sensors: set[str] = set()

    def run_once(self) -> tuple[list[SensorReading], float | None]:
        readings = self._backend.read_temperatures()
        peak = compute_peak(readings, self._warned_sensors)
        return readings, peak

    def run_forever(self) -> None:
        try:
            while True:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                readings, peak = self.run_once()
                print(timestamp)
                for reading in readings:
                    print(f"  {reading.name}: {reading.value_celsius}°C")
                if peak is not None:
                    print(f"Peak: {peak}°C")
                else:
                    print("Peak: unknown")
                print()
                time.sleep(self._poll_interval)
        except KeyboardInterrupt:
            pass


def main() -> None:
    bridge = LhmBridge()
    try:
        bridge.open()
    except LhmDllNotFoundError as exc:
        print(str(exc))
        sys.exit(1)
    TelemetryPoller(bridge).run_forever()


if __name__ == "__main__":
    main()
