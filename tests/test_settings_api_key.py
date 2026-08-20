"""Settings dialog API key field tests."""

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
            "callmebot_api_key": "secret-key-9046",
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


class FakeEntry:
    instances: list["FakeEntry"] = []

    def __init__(self, master: Any, textvariable: FakeVar, **kwargs: Any) -> None:
        self.textvariable = textvariable
        self.show = kwargs.get("show")
        self.width = kwargs.get("width")
        FakeEntry.instances.append(self)

    def config(self, **kwargs: Any) -> None:
        if "show" in kwargs:
            self.show = kwargs["show"]

    def grid(self, **kwargs: Any) -> None:
        return None

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeButton:
    instances: list["FakeButton"] = []

    def __init__(self, master: Any, text: str, width: int, command: Any) -> None:
        self.text = text
        self.command = command
        FakeButton.instances.append(self)

    def config(self, **kwargs: Any) -> None:
        if "text" in kwargs:
            self.text = kwargs["text"]

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeTkModule:
    StringVar = FakeVar
    BooleanVar = FakeVar
    Entry = FakeEntry
    Button = FakeButton

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

    class Checkbutton:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def pack(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Tk:
        def title(self, *_args: Any) -> None:
            pass

        def resizable(self, *_args: Any) -> None:
            pass

        def protocol(self, *_args: Any) -> None:
            pass

        def mainloop(self) -> None:
            pass


def _api_key_entry() -> FakeEntry:
    for entry in FakeEntry.instances:
        if entry.show == "*":
            return entry
    raise AssertionError("API key entry not found")


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_prefills_api_key_masked():
    FakeEntry.instances.clear()
    FakeButton.instances.clear()

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    api_entry = _api_key_entry()
    assert api_entry.textvariable.get() == "secret-key-9046"
    eye_buttons = [btn for btn in FakeButton.instances if btn.text == "\U0001f441"]
    assert len(eye_buttons) == 1


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_eye_button_toggles_api_key_visibility():
    FakeEntry.instances.clear()
    FakeButton.instances.clear()

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    eye = next(btn for btn in FakeButton.instances if btn.text == "\U0001f441")
    entry = _api_key_entry()

    eye.command()
    assert entry.show == ""
    assert eye.text == "Hide"

    eye.command()
    assert entry.show == "*"
    assert eye.text == "\U0001f441"
