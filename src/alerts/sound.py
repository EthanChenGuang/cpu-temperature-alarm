"""Injectable sound backends for intermittent local alert beeps."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BeepPattern:
    burst_count: int
    burst_gap_ms: int
    interval_seconds: float


class SoundBackend(Protocol):
    def start_beep(
        self,
        frequency_hz: int,
        duration_ms: int,
        *,
        pattern: BeepPattern,
    ) -> None: ...

    def stop_beep(self) -> None: ...


class MockSoundBackend:
    """Test double that records beep state without winsound."""

    def __init__(self) -> None:
        self.is_beeping = False
        self.start_count = 0
        self.stop_count = 0
        self.last_frequency_hz: int | None = None
        self.last_duration_ms: int | None = None
        self.last_pattern: BeepPattern | None = None

    def start_beep(
        self,
        frequency_hz: int,
        duration_ms: int,
        *,
        pattern: BeepPattern,
    ) -> None:
        if not self.is_beeping:
            self.start_count += 1
        self.is_beeping = True
        self.last_frequency_hz = frequency_hz
        self.last_duration_ms = duration_ms
        self.last_pattern = pattern

    def stop_beep(self) -> None:
        if self.is_beeping:
            self.stop_count += 1
        self.is_beeping = False


class WinsoundBackend:
    """Windows PC speaker — short burst cycles with pauses between cycles."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._pattern_key: tuple[int, int, int, int, float] | None = None

    def start_beep(
        self,
        frequency_hz: int,
        duration_ms: int,
        *,
        pattern: BeepPattern,
    ) -> None:
        pattern_key = (
            frequency_hz,
            duration_ms,
            pattern.burst_count,
            pattern.burst_gap_ms,
            pattern.interval_seconds,
        )
        with self._lock:
            if (
                self._thread is not None
                and self._thread.is_alive()
                and self._pattern_key == pattern_key
            ):
                return
            self._stop_event.set()
            old_thread = self._thread

        if old_thread is not None and old_thread.is_alive():
            old_thread.join(timeout=2.0)

        with self._lock:
            self._stop_event.clear()
            self._pattern_key = pattern_key
            self._thread = threading.Thread(
                target=self._beep_loop,
                args=(frequency_hz, duration_ms, pattern),
                daemon=True,
                name="alert-beep",
            )
            self._thread.start()

    def stop_beep(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._pattern_key = None
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._thread = None

    def _beep_loop(self, frequency_hz: int, duration_ms: int, pattern: BeepPattern) -> None:
        import winsound  # noqa: PLC0415 — lazy import per D-08

        gap_seconds = pattern.burst_gap_ms / 1000.0
        while not self._stop_event.is_set():
            for index in range(pattern.burst_count):
                if self._stop_event.is_set():
                    return
                winsound.Beep(frequency_hz, duration_ms)
                if index + 1 < pattern.burst_count and self._stop_event.wait(gap_seconds):
                    return
            if self._stop_event.wait(pattern.interval_seconds):
                return
