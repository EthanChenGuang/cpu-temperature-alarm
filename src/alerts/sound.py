"""Injectable sound backends for local alert beep."""

from __future__ import annotations

import threading
from typing import Protocol


class SoundBackend(Protocol):
    def start_beep(self, frequency_hz: int, duration_ms: int) -> None: ...

    def stop_beep(self) -> None: ...


class MockSoundBackend:
    """Test double that records beep state without winsound."""

    def __init__(self) -> None:
        self.is_beeping = False
        self.start_count = 0
        self.stop_count = 0
        self.last_frequency_hz: int | None = None
        self.last_duration_ms: int | None = None

    def start_beep(self, frequency_hz: int, duration_ms: int) -> None:
        if not self.is_beeping:
            self.start_count += 1
        self.is_beeping = True
        self.last_frequency_hz = frequency_hz
        self.last_duration_ms = duration_ms

    def stop_beep(self) -> None:
        if self.is_beeping:
            self.stop_count += 1
        self.is_beeping = False


class WinsoundBackend:
    """Windows PC speaker beep loop using winsound (lazy import)."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start_beep(self, frequency_hz: int, duration_ms: int) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._beep_loop,
                args=(frequency_hz, duration_ms),
                daemon=True,
                name="alert-beep",
            )
            self._thread.start()

    def stop_beep(self) -> None:
        with self._lock:
            self._stop_event.set()
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._thread = None

    def _beep_loop(self, frequency_hz: int, duration_ms: int) -> None:
        import winsound  # noqa: PLC0415 — lazy import per D-08

        while not self._stop_event.is_set():
            winsound.Beep(frequency_hz, duration_ms)
            if self._stop_event.wait(0.1):
                break
