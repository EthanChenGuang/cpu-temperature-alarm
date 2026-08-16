"""System tray orchestration — telemetry poll, icon, menu, and alerts."""

from __future__ import annotations

import logging
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from PIL import Image

from src.alerts.engine import AlertEngine, AlertState
from src.alerts.sound import SoundBackend, WinsoundBackend
from src.alerts.whatsapp import CallMeBotClient, WhatsAppClient
from src.config.loader import load_config
from src.config.schema import AppConfig
from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBackend, LhmBridge, SensorReading
from src.telemetry.sensor_reader import TelemetryPoller
from src.ui.icon_renderer import peak_display_text, render_peak_icon
from src.ui.settings import show_settings_dialog

logger = logging.getLogger(__name__)

__all__ = ["MockTrayController", "PystrayTrayController", "TemperatureTrayApp", "main"]


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
        self._initial_image = render_peak_icon(None, size=16)

    def start(self, *, on_ready: Callable[[], None] | None = None) -> None:
        import pystray

        self._pystray = pystray
        self._icon = pystray.Icon(self._name, self._initial_image, "CPU Temp", menu=pystray.Menu())
        if on_ready is not None:
            threading.Thread(target=on_ready, daemon=True).start()
        self._icon.run()

    def update_icon(self, image: Image.Image, title: str) -> None:
        if self._icon is not None:
            self._icon.icon = image
            self._icon.title = title

    def update_menu(self, items: list[MenuItemSpec]) -> None:
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
                    label=f"{reading.name}: {reading.value_celsius:.0f}°C",
                    action=None,
                    enabled=False,
                )
            )
        if not readings:
            items.append(MenuItemSpec(label="No sensors detected", enabled=False))
        items.append(MenuItemSpec(separator=True))
        items.append(MenuItemSpec(label="Open Settings", action=self._open_settings))
        items.append(MenuItemSpec(label="Exit", action=self._exit))
        return items

    def _open_settings(self) -> None:
        updated = show_settings_dialog(self._config)
        if updated is not None:
            self._apply_config(updated)

    def _apply_config(self, config: AppConfig) -> None:
        self._config = config
        self._poller = TelemetryPoller(self._backend, config.poll_interval_seconds)
        self._engine = AlertEngine(config, self._sound, self._whatsapp)
        if isinstance(self._whatsapp, CallMeBotClient):
            self._whatsapp.update_credentials(config.whatsapp_phone, config.callmebot_api_key)
        logger.info("Config reloaded — threshold=%s°C", config.threshold_celsius)

    def _exit(self) -> None:
        logger.info("Exit requested — shutting down tray app")
        self._stop_event.set()
        self._sound.stop_beep()
        self._tray.stop()

    def _handle_poll(self, readings: list[SensorReading], peak: float | None) -> None:
        self._engine.process_peak(peak)
        alerting = self._engine.state in (AlertState.ALERTING, AlertState.COOLDOWN)
        peak_text = peak_display_text(peak)
        title = f"Peak: {peak_text}°C" if peak is not None else "Peak: unknown"
        image = render_peak_icon(peak, size=16, alerting=alerting)
        self._tray.update_icon(image, title)
        self._last_peak_text = peak_text
        self._tray.update_menu(self._build_menu_items(readings))

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_config()
    bridge = LhmBridge()
    try:
        bridge.open()
    except LhmDllNotFoundError as exc:
        print(str(exc))
        sys.exit(1)

    app = TemperatureTrayApp(
        config,
        bridge,
        WinsoundBackend(),
        CallMeBotClient(config.whatsapp_phone, config.callmebot_api_key),
    )
    app.run()


if __name__ == "__main__":
    main()
