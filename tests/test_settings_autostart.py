"""Settings dialog autostart checkbox tests."""

from __future__ import annotations

import sys
import threading
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


class FakeEntry:
    def __init__(self, master: Any, textvariable: FakeVar, **kwargs: Any) -> None:
        self.textvariable = textvariable
        self.show = kwargs.get("show")

    def config(self, **kwargs: Any) -> None:
        if "show" in kwargs:
            self.show = kwargs["show"]

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeButton:
    def __init__(self, master: Any, text: str, width: int, command: Any) -> None:
        self.text = text
        self.command = command

    def config(self, **kwargs: Any) -> None:
        if "text" in kwargs:
            self.text = kwargs["text"]

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeTkModule:
    StringVar = FakeVar
    BooleanVar = FakeVar

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
            self._widget = FakeEntry(master, textvariable, **kwargs)

        def grid(self, **kwargs: Any) -> None:
            return None

        def pack(self, **kwargs: Any) -> None:
            return self._widget.pack(**kwargs)

        def config(self, **kwargs: Any) -> None:
            return self._widget.config(**kwargs)

    class Button:
        def __init__(self, master: Any, text: str, width: int, command: Any) -> None:
            self._widget = FakeButton(master, text, width, command)

        def pack(self, **kwargs: Any) -> None:
            return self._widget.pack(**kwargs)

        def config(self, **kwargs: Any) -> None:
            return self._widget.config(**kwargs)

    Checkbutton = FakeCheckbutton

    class Tk:
        def title(self, *_args: Any) -> None:
            pass

        def resizable(self, *_args: Any) -> None:
            pass

        def protocol(self, *_args: Any) -> None:
            pass

        def after(self, _delay: int, callback: Any) -> None:
            callback()

        def after_idle(self, callback: Any) -> None:
            callback()

        def update_idletasks(self) -> None:
            pass

        def mainloop(self) -> None:
            pass


@patch("src.ui.settings.sys.platform", "win32")
def test_settings_dialog_renders_autostart_checkbox():
    FakeCheckbutton.instances.clear()
    autostart_state = {"enabled": False}

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: autostart_state["enabled"],
        autostart_set_enabled=lambda enabled: (
            autostart_state.update(enabled=enabled) or (True, "ok")
        ),
    )

    assert len(FakeCheckbutton.instances) >= 2
    autostart_checkbox = next(cb for cb in FakeCheckbutton.instances if cb.text == "Start with Windows")
    assert autostart_checkbox.text == "Start with Windows"


@patch("src.ui.settings.sys.platform", "win32")
def test_settings_dialog_autostart_toggle_calls_setter():
    FakeCheckbutton.instances.clear()
    calls: list[bool] = []
    done = threading.Event()

    def set_autostart(enabled: bool) -> tuple[bool, str]:
        calls.append(enabled)
        done.set()
        return True, "ok"

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=set_autostart,
    )

    checkbox = next(cb for cb in FakeCheckbutton.instances if cb.text == "Start with Windows")
    checkbox.variable.set(True)
    checkbox.command()

    assert done.wait(timeout=2.0)
    assert calls == [True]
