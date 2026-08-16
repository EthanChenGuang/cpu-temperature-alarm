"""Telemetry sensor polling and peak temperature computation.

Poll interval defaults to 3 seconds, matching TELE-01/TELE-02 cadence and
``config/config.example.json`` ``poll_interval_seconds``.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBackend, LhmBridge, SensorReading

__all__ = ["SensorReading", "SensorSnapshot", "TelemetryPoller", "compute_peak", "main", "read_sensors"]

logger = logging.getLogger(__name__)

MIN_VALID_C = 0
MAX_VALID_C = 150


@dataclass(frozen=True)
class SensorSnapshot:
    readings: list[SensorReading]
    peak_temp: float | None


def compute_peak(
    readings: list[SensorReading],
    warned_sensors: set[str] | None = None,
) -> float | None:
    """Return max valid temperature or None when no valid readings remain."""
    valid: list[float] = []
    warned = warned_sensors if warned_sensors is not None else set()

    for reading in readings:
        if reading.value_celsius <= MIN_VALID_C or reading.value_celsius > MAX_VALID_C:
            if reading.name not in warned:
                logger.warning(
                    "Invalid temperature for %s: %s°C (valid range: >0 and <=150)",
                    reading.name,
                    reading.value_celsius,
                )
                warned.add(reading.name)
            continue
        warned.discard(reading.name)
        valid.append(reading.value_celsius)

    return max(valid) if valid else None


def read_sensors(backend: LhmBackend) -> SensorSnapshot:
    """Read all temperature sensors once and return readings with peak."""
    readings = backend.read_temperatures()
    peak = compute_peak(readings)
    return SensorSnapshot(readings=readings, peak_temp=peak)


class TelemetryPoller:
    def __init__(self, backend: LhmBackend, poll_interval_seconds: float = 3) -> None:
        self._backend = backend
        self._poll_interval = poll_interval_seconds
        self._warned_sensors: set[str] = set()
        self._logged_empty = False

    def run_once(self) -> tuple[list[SensorReading], float | None]:
        readings = self._backend.read_temperatures()
        if readings:
            self._logged_empty = False
        peak = compute_peak(readings, self._warned_sensors)
        return readings, peak

    def run_forever(self) -> None:
        try:
            while True:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                readings, peak = self.run_once()

                if not readings and not self._logged_empty:
                    print("No temperature sensors detected — continuing to poll every 3s")
                    self._logged_empty = True

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
