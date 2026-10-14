"""System tray orchestration — telemetry poll, icon, menu, and alerts."""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from PIL import Image

from src.alerts.engine import AlertEngine, AlertState
from src.alerts.sound import SoundBackend
from src.alerts.whatsapp import CallMeBotClient, WhatsAppClient
from src.config.loader import load_config
from src.config.schema import AppConfig
from src.paths import app_root
from src.telemetry.lhm_wrapper import LhmBackend, SensorReading
from src.telemetry.sensor_reader import TelemetryPoller
from src.ui.icon_renderer import TRAY_ICON_SIZE, peak_display_text, render_tray_icon

logger = logging.getLogger(__name__)

__all__ = ["MockTrayController", "PystrayTrayController", "TemperatureTrayApp", "main"]


def _settings_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--settings"]
    return [sys.executable, "-m", "src.ui.settings_cli"]


def _run_settings_subprocess() -> None:
    subprocess.run(
        _settings_command(),
        cwd=app_root(),
        check=False,
    )


@dataclass
class MenuItemSpec:
    label: str = ""
    action: Callable[[], None] | None = None
    enabled: bool = True
    separator: bool = False


class TrayIconController(Protocol):
    def start(self, *, on_ready: Callable[[], None] | None = None) -> None: ...

    def update_icon(self, image: Image.Image, title: str) -> None: ...

    def update_menu(self, items: list[MenuItemSpec]) -> None: ...

    def stop(self) -> None: ...


@dataclass
class MockTrayController:
    """Test double for pystray — records icon/menu updates without a display server."""

    images: list[Image.Image] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    menus: list[list[MenuItemSpec]] = field(default_factory=list)
    stopped: bool = False
    _on_ready: Callable[[], None] | None = None

    def start(self, *, on_ready: Callable[[], None] | None = None) -> None:
        self._on_ready = on_ready
        if on_ready is not None:
            on_ready()

    def update_icon(self, image: Image.Image, title: str) -> None:
        self.images.append(image.copy())
        self.titles.append(title)

    def update_menu(self, items: list[MenuItemSpec]) -> None:
        self.menus.append(list(items))

    def stop(self) -> None:
        self.stopped = True


class PystrayTrayController:
    """Production tray controller using pystray."""

    def __init__(self, name: str = "cpu-temp-alert") -> None:
        self._name = name
        self._icon: Any = None
        self._pystray: Any = None
        self._menu_items: list[MenuItemSpec] = []
        self._initial_image = render_tray_icon(None, size=TRAY_ICON_SIZE)

    def _apply_native_menu(self, items: list[MenuItemSpec]) -> None:
        if self._icon is None or self._pystray is None:
            return
        menu_items: list[Any] = []
        for spec in items:
            if spec.separator:
                menu_items.append(self._pystray.Menu.SEPARATOR)
                continue
            menu_items.append(
                self._pystray.MenuItem(
                    spec.label,
                    spec.action,
                    enabled=spec.enabled,
                )
            )
        self._icon.menu = self._pystray.Menu(*menu_items) if menu_items else self._pystray.Menu()
        self._icon.update_menu()

    def _patch_nonblocking_menu(self) -> None:
        """Replace Win32 TrackPopupMenu with a non-modal Tk popup on right-click."""
        if sys.platform != "win32" or self._icon is None:
            return

        icon = self._icon
        original_on_notify = icon._on_notify

        def patched_on_notify(wparam: int, lparam: int) -> None:
            from pystray._util import win32

            if lparam == win32.WM_LBUTTONUP:
                icon()
            elif lparam == win32.WM_RBUTTONUP:
                try:
                    from ctypes import byref, wintypes

                    point = wintypes.POINT()
                    win32.GetCursorPos(byref(point))
                    from src.ui.tray_popup import show_tray_popup_menu

                    items = list(self._menu_items)
                    if not items:
                        if icon._menu_handle:
                            original_on_notify(wparam, lparam)
                        return
                    show_tray_popup_menu(
                        items,
                        x=point.x,
                        y=point.y,
                        icon=icon,
                    )
                except Exception:
                    logger.exception("Custom tray popup failed — falling back to native menu")
                    if icon._menu_handle and lparam == win32.WM_RBUTTONUP:
                        original_on_notify(wparam, lparam)
            else:
                original_on_notify(wparam, lparam)

        icon._on_notify = patched_on_notify
        # Keep a native menu built so we can fall back if the Tk popup fails.
        self._apply_native_menu(self._menu_items)

    def start(self, *, on_ready: Callable[[], None] | None = None) -> None:
        import pystray

        self._pystray = pystray
        self._icon = pystray.Icon(self._name, self._initial_image, "CPU Temp", menu=pystray.Menu())

        def setup(icon: Any) -> None:
            icon.visible = True
            if sys.platform == "win32":
                self._patch_nonblocking_menu()
            if on_ready is not None:
                on_ready()

        self._icon.run(setup=setup)

    def update_icon(self, image: Image.Image, title: str) -> None:
        if self._icon is not None:
            self._icon.icon = image
            self._icon.title = title

    def update_menu(self, items: list[MenuItemSpec]) -> None:
        self._menu_items = list(items)
        if sys.platform == "win32":
            self._apply_native_menu(items)
            return
        if self._icon is None or self._pystray is None:
            return
        menu_items: list[Any] = []
        for spec in items:
            if spec.separator:
                menu_items.append(self._pystray.Menu.SEPARATOR)
                continue
            menu_items.append(
                self._pystray.MenuItem(
                    spec.label,
                    spec.action,
                    enabled=spec.enabled,
                )
            )
        self._icon.menu = self._pystray.Menu(*menu_items)
        self._icon.update_menu()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()


class TemperatureTrayApp:
    """Poll telemetry, update tray icon/menu, and drive alert engine."""

    def __init__(
        self,
        config: AppConfig,
        backend: LhmBackend,
        sound: SoundBackend,
        whatsapp: WhatsAppClient,
        *,
        tray_controller: TrayIconController | None = None,
    ) -> None:
        self._config = config
        self._backend = backend
        self._sound = sound
        self._whatsapp = whatsapp
        self._tray = tray_controller or PystrayTrayController()
        self._poller = TelemetryPoller(backend, config.poll_interval_seconds)
        self._engine = AlertEngine(config, sound, whatsapp)
        self._stop_event = threading.Event()
        self._poll_thread: threading.Thread | None = None
        self._last_peak_text: str | None = None

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def tray_controller(self) -> TrayIconController:
        return self._tray

    def _build_menu_items(self, readings: list[SensorReading]) -> list[MenuItemSpec]:
        items: list[MenuItemSpec] = []
        for reading in readings:
            items.append(
                MenuItemSpec(
                    label=f"{reading.name}: {reading.value_celsius:.1f}°C",
                    action=None,
                    enabled=False,
                )
            )
        if not readings:
            items.append(MenuItemSpec(label="No sensors detected", enabled=False))
        items.append(MenuItemSpec(separator=True))
        if self._config.sound_alerts_enabled:
            if self._engine.is_muted:
                minutes = max(1, self._config.mute_duration_seconds // 60)
                items.append(MenuItemSpec(label=f"Sound muted ({minutes} min)", enabled=False))
            else:
                minutes = max(1, self._config.mute_duration_seconds // 60)
                items.append(MenuItemSpec(label=f"Mute sound {minutes} min", action=self._mute_alerts))
        items.append(MenuItemSpec(label="Open Settings", action=self._open_settings))
        items.append(MenuItemSpec(label="Exit", action=self._exit))
        return items

    def _open_settings(self, icon: Any, item: Any) -> None:
        _run_settings_subprocess()
        self._apply_config(load_config())

    def _mute_alerts(self, icon: Any, item: Any) -> None:
        self._engine.mute(self._config.mute_duration_seconds)
        logger.info("Tray mute requested for %s seconds", self._config.mute_duration_seconds)

    def _apply_config(self, config: AppConfig) -> None:
        self._config = config
        self._poller = TelemetryPoller(self._backend, config.poll_interval_seconds)
        self._engine.update_config(config)
        if isinstance(self._whatsapp, CallMeBotClient):
            self._whatsapp.update_credentials(config.whatsapp_phone, config.callmebot_api_key)
        logger.info("Config reloaded — threshold=%s°C", config.threshold_celsius)

    def _exit(self, icon: Any, item: Any) -> None:
        logger.info("Exit requested — shutting down tray app")
        self._stop_event.set()
        self._sound.stop_beep()
        icon.stop()

    def _handle_poll(self, readings: list[SensorReading], peak: float | None) -> None:
        self._engine.process_peak(peak)
        alerting = self._engine.state in (AlertState.ALERTING, AlertState.COOLDOWN)
        peak_text = peak_display_text(peak)
        title = f"Peak: {peak:.1f}°C" if peak is not None else "Peak: unknown"
        image = render_tray_icon(peak, size=TRAY_ICON_SIZE, alerting=alerting)
        self._tray.update_icon(image, title)
        self._last_peak_text = peak_text
        self._tray.update_menu(self._build_menu_items(readings))

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            fresh = load_config()
            if fresh.poll_interval_seconds != self._config.poll_interval_seconds:
                self._poller = TelemetryPoller(self._backend, fresh.poll_interval_seconds)
            self._config = fresh
            self._engine.update_config(fresh)
            if isinstance(self._whatsapp, CallMeBotClient):
                self._whatsapp.update_credentials(
                    fresh.whatsapp_phone,
                    fresh.callmebot_api_key,
                )
            readings, peak = self._poller.run_once()
            self._handle_poll(readings, peak)
            if self._stop_event.wait(self._config.poll_interval_seconds):
                break

    def run(self) -> None:
        def on_ready() -> None:
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()
            readings, peak = self._poller.run_once()
            self._handle_poll(readings, peak)

        self._tray.start(on_ready=on_ready)


def main() -> None:
    """Backward-compatible entry — delegates to production src.main."""
    from src.main import main as production_main

    production_main()


if __name__ == "__main__":
    main()
