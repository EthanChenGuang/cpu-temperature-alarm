"""Settings dialog sound alerts checkbox tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from src.config.schema import config_from_dict
from src.ui.settings import show_settings_dialog


def _make_config():
    return config_from_dict(
        {
            "threshold_celsius": 85,
            "critical_tiers_celsius": [90, 95],
            "cooldown_seconds": 180,
            "poll_interval_seconds": 3,
            "whatsapp_phone": "+15551234567",
            "callmebot_api_key": "test-key",
            "beep_frequency_hz": 1000,
            "beep_duration_ms": 500,
            "sound_alerts_enabled": True,
        }
    )


class FakeVar:
    def __init__(self, value: Any = "") -> None:
        self._value = value

    def get(self) -> Any:
        return self._value

    def set(self, value: Any) -> None:
        self._value = value


class FakeCheckbutton:
    instances: list["FakeCheckbutton"] = []

    def __init__(self, master: Any, text: str, variable: FakeVar, command: Any = None) -> None:
        self.text = text
        self.variable = variable
        self.command = command
        FakeCheckbutton.instances.append(self)

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeTkModule:
    StringVar = FakeVar
    BooleanVar = FakeVar
    Checkbutton = FakeCheckbutton

    class Frame:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def grid(self, *args: Any, **kwargs: Any) -> None:
            pass

        def grid_remove(self) -> None:
            pass

        def pack(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Label:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def grid(self, *args: Any, **kwargs: Any) -> None:
            pass

        def pack(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Entry:
        def __init__(self, master: Any, textvariable: FakeVar, **kwargs: Any) -> None:
            pass

        def grid(self, **kwargs: Any) -> None:
            return None

        def pack(self, **kwargs: Any) -> None:
            return None

        def config(self, **kwargs: Any) -> None:
            return None

    class Button:
        def __init__(self, master: Any, text: str, width: int, command: Any) -> None:
            pass

        def pack(self, **kwargs: Any) -> None:
            return None

        def config(self, **kwargs: Any) -> None:
            return None

    class Tk:
        def title(self, *_args: Any) -> None:
            pass

        def resizable(self, *_args: Any) -> None:
            pass

        def protocol(self, *_args: Any) -> None:
            pass

        def update_idletasks(self) -> None:
            pass

        def after(self, _delay: int, callback: Any) -> None:
            callback()

        def mainloop(self) -> None:
            pass


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_dialog_renders_sound_alerts_checkbox():
    FakeCheckbutton.instances.clear()

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    sound_checkbox = next(cb for cb in FakeCheckbutton.instances if cb.text == "Sound alerts")
    assert sound_checkbox.variable.get() is True
