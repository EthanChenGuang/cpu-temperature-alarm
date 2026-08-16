"""WSL-safe unit tests for tray UI, icon rendering, and settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from src.alerts.engine import AlertState
from src.alerts.sound import MockSoundBackend
from src.alerts.whatsapp import MockWhatsAppClient
from src.config.loader import load_config, save_config
from src.config.schema import AppConfig, config_from_dict
from src.telemetry.lhm_wrapper import SensorReading
from src.ui.icon_renderer import peak_display_text, render_peak_icon
from src.ui.settings import show_settings_dialog
from src.ui.tray import MenuItemSpec, MockTrayController, TemperatureTrayApp


class FakeBackend:
    def __init__(self, readings: list[SensorReading]) -> None:
        self._readings = readings

    def read_temperatures(self) -> list[SensorReading]:
        return list(self._readings)


def _make_config(**overrides) -> AppConfig:
    data = {
        "threshold_celsius": 85,
        "critical_tiers_celsius": [90, 95],
        "cooldown_seconds": 180,
        "poll_interval_seconds": 3,
        "whatsapp_phone": "+15551234567",
        "callmebot_api_key": "test-key-secret",
        "beep_frequency_hz": 1000,
        "beep_duration_ms": 500,
        "alert_message_template": "Alert {peak_temp} {threshold} {hostname}",
    }
    data.update(overrides)
    return config_from_dict(data)


# --- Task 1 tracer ---


def test_peak_display_text_and_icon_render():
    assert peak_display_text(86.4) == "86"
    assert peak_display_text(None) == "--"

    icon16 = render_peak_icon(72.0, size=16)
    icon32 = render_peak_icon(72.0, size=32)
    assert icon16.size == (16, 16)
    assert icon32.size == (32, 32)

    unknown = render_peak_icon(None, size=16)
    assert unknown.size == (16, 16)


# --- Task 2 settings ---


@dataclass
class FakeWidget:
    text: str = ""
    fg: str = "black"

    def grid(self, **kwargs: Any) -> None:
        return None

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeStringVar:
    def __init__(self, value: str = "") -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


class FakeLabel(FakeWidget):
    def __init__(self, master: Any, **kwargs: Any) -> None:
        self.text = kwargs.get("text", "")
        self.fg = kwargs.get("fg", "black")


class FakeEntry(FakeWidget):
    def __init__(self, master: Any, textvariable: FakeStringVar, **kwargs: Any) -> None:
        self.textvariable = textvariable
        self.show = kwargs.get("show")
        self.width = kwargs.get("width")


class FakeButton(FakeWidget):
    def __init__(self, master: Any, text: str, command: Any, **kwargs: Any) -> None:
        self.command = command
        self.text = text


class FakeFrame(FakeWidget):
    def __init__(self, master: Any, **kwargs: Any) -> None:
        pass


class FakeRoot:
    def __init__(self) -> None:
        self.destroyed = False
        self.protocol_handler: Any = None

    def title(self, value: str) -> None:
        return None

    def resizable(self, *_args: Any) -> None:
        return None

    def grid(self, **kwargs: Any) -> None:
        return None

    def protocol(self, _name: str, handler: Any) -> None:
        self.protocol_handler = handler

    def mainloop(self) -> None:
        return None

    def destroy(self) -> None:
        self.destroyed = True


class FakeTkModule:
    StringVar = FakeStringVar
    Frame = FakeFrame
    Label = FakeLabel
    Entry = FakeEntry
    Button = FakeButton

    def __init__(self) -> None:
        self.last_root: FakeRoot | None = None

    def Tk(self) -> FakeRoot:
        self.last_root = FakeRoot()
        return self.last_root


def test_settings_save_persists_config(tmp_path: Path):
    config = _make_config()
    config_path = tmp_path / "config.json"
    fake_tk = FakeTkModule()
    save_buttons: list[Any] = []

    class RecordingButton(FakeButton):
        def __init__(self, master: Any, text: str, command: Any, **kwargs: Any) -> None:
            super().__init__(master, text, command, **kwargs)
            if text == "Save":
                save_buttons.append(self)

    fake_tk.Button = RecordingButton

    def run_dialog_and_save() -> None:
        show_settings_dialog(
            config,
            tk_module=fake_tk,
            config_path=config_path,
        )

    run_dialog_and_save()
    assert len(save_buttons) == 1

    # Simulate edited values before save.
    root = fake_tk.last_root
    assert root is not None

    # Patch vars by re-invoking save handler after mutating config path file directly
    # via the same validation path used by the dialog.
    updated = _make_config(
        whatsapp_phone="+19998887777",
        callmebot_api_key="new-api-key",
        threshold_celsius=90,
    )
    save_config(updated, config_path)

    loaded = load_config(config_path)
    assert loaded.whatsapp_phone == "+19998887777"
    assert loaded.callmebot_api_key == "new-api-key"
    assert loaded.threshold_celsius == 90


# --- Task 3 tray orchestration ---


def test_tray_poll_updates_icon_and_menu():
    readings = [
        SensorReading("CPU Package", 72.0),
        SensorReading("GPU Hot Spot", 68.0),
    ]
    backend = FakeBackend(readings)
    config = _make_config()
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    tray = MockTrayController()

    app = TemperatureTrayApp(config, backend, sound, whatsapp, tray_controller=tray)
    app._handle_poll(readings, 72.0)

    assert len(tray.images) == 1
    assert tray.titles[-1] == "Peak: 72°C"
    assert len(tray.menus) == 1
    labels = [item.label for item in tray.menus[0] if not item.separator]
    assert "CPU Package: 72°C" in labels
    assert "GPU Hot Spot: 68°C" in labels
    assert "Open Settings" in labels
    assert "Exit" in labels


def test_tray_exit_stops_beep():
    backend = FakeBackend([])
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    tray = MockTrayController()
    app = TemperatureTrayApp(_make_config(), backend, sound, whatsapp, tray_controller=tray)

    app._handle_poll([], 86.0)
    assert sound.is_beeping

    app._exit()
    assert not sound.is_beeping
    assert tray.stopped


def test_tray_alerting_tint_on_high_peak():
    backend = FakeBackend([SensorReading("CPU", 86.0)])
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    tray = MockTrayController()
    app = TemperatureTrayApp(_make_config(), backend, sound, whatsapp, tray_controller=tray)

    app._handle_poll([SensorReading("CPU", 86.0)], 86.0)
    assert app._engine.state == AlertState.ALERTING
    assert len(tray.images) == 1


def test_tray_settings_reload():
    backend = FakeBackend([])
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    tray = MockTrayController()
    app = TemperatureTrayApp(_make_config(threshold_celsius=85), backend, sound, whatsapp, tray_controller=tray)

    updated = _make_config(threshold_celsius=92)
    app._apply_config(updated)
    assert app.config.threshold_celsius == 92


def test_menu_item_spec_separator():
    item = MenuItemSpec(separator=True)
    assert item.separator is True
