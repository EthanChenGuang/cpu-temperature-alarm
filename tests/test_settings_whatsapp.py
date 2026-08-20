"""Settings dialog WhatsApp message checkbox tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from src.config.loader import load_config
from src.config.schema import config_from_dict, config_to_dict
from src.ui.settings import show_settings_dialog


def _make_config(**overrides):
    data = {
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
    data.update(overrides)
    return config_from_dict(data)


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


class FakeButton:
    instances: list["FakeButton"] = []

    def __init__(self, master: Any, text: str, width: int, command: Any) -> None:
        self.text = text
        self.command = command
        FakeButton.instances.append(self)

    def pack(self, **kwargs: Any) -> None:
        return None

    def config(self, **kwargs: Any) -> None:
        return None


class FakeFrame:
    instances: list["FakeFrame"] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.visible = True
        FakeFrame.instances.append(self)

    def grid(self, *args: Any, **kwargs: Any) -> None:
        self.visible = True

    def grid_remove(self) -> None:
        self.visible = False

    def pack(self, **kwargs: Any) -> None:
        return None


class FakeEntry:
    instances: list["FakeEntry"] = []

    def __init__(self, master: Any, textvariable: FakeVar, **kwargs: Any) -> None:
        self.master = master
        self.textvariable = textvariable
        self.show = kwargs.get("show")
        self.width = kwargs.get("width")
        FakeEntry.instances.append(self)

    def grid(self, **kwargs: Any) -> None:
        return None

    def pack(self, **kwargs: Any) -> None:
        return None

    def config(self, **kwargs: Any) -> None:
        if "show" in kwargs:
            self.show = kwargs["show"]


class FakeTkModule:
    StringVar = FakeVar
    BooleanVar = FakeVar
    Checkbutton = FakeCheckbutton
    Button = FakeButton
    Frame = FakeFrame
    Entry = FakeEntry

    class Label:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def grid(self, *args: Any, **kwargs: Any) -> None:
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

        def update_idletasks(self) -> None:
            pass

        def after(self, _delay: int, callback: Any) -> None:
            callback()

        def destroy(self) -> None:
            pass

        def mainloop(self) -> None:
            pass


def _whatsapp_checkbox() -> FakeCheckbutton:
    return next(cb for cb in FakeCheckbutton.instances if cb.text == "WhatsApp message")


def _hidden_frames() -> list[FakeFrame]:
    return [frame for frame in FakeFrame.instances if not frame.visible]


def _api_key_entry() -> FakeEntry:
    for entry in FakeEntry.instances:
        if entry.show == "*":
            return entry
    raise AssertionError("API key entry not found")


def _phone_entry() -> FakeEntry:
    for entry in FakeEntry.instances:
        if entry.width == 32:
            return entry
    raise AssertionError("Phone entry not found")


def _reset_fakes() -> None:
    FakeCheckbutton.instances.clear()
    FakeButton.instances.clear()
    FakeFrame.instances.clear()
    FakeEntry.instances.clear()


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_dialog_renders_whatsapp_message_checkbox():
    _reset_fakes()

    config = _make_config()
    show_settings_dialog(
        config,
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    checkbox = _whatsapp_checkbox()
    assert checkbox.variable.get() is True
    assert config.whatsapp_alerts_enabled is True
    assert _api_key_entry().show == "*"
    assert _phone_entry().textvariable.get() == "+15551234567"
    assert _hidden_frames() == []


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_save_persists_whatsapp_alerts_enabled_false(tmp_path):
    _reset_fakes()

    config_path = tmp_path / "config.json"

    class SavingTkModule(FakeTkModule):
        class Tk(FakeTkModule.Tk):
            def mainloop(self) -> None:
                _whatsapp_checkbox().variable.set(False)
                save = next(btn for btn in FakeButton.instances if btn.text == "Save")
                save.command()

    show_settings_dialog(
        _make_config(),
        tk_module=SavingTkModule(),
        config_path=config_path,
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    loaded = load_config(config_path)
    assert loaded.whatsapp_alerts_enabled is False
    assert loaded.whatsapp_phone == "+15551234567"
    assert loaded.callmebot_api_key == "test-key"
    serialized = config_to_dict(loaded)
    assert serialized["whatsapp_alerts_enabled"] is False
    assert serialized["whatsapp_phone"] == "+15551234567"
    assert serialized["callmebot_api_key"] == "test-key"


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_hides_credential_fields_when_whatsapp_idle():
    _reset_fakes()

    show_settings_dialog(
        _make_config(whatsapp_alerts_enabled=False),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    assert _whatsapp_checkbox().variable.get() is False
    assert _hidden_frames(), "credential fields frame should be grid_removed when idle"
    assert _api_key_entry().textvariable.get() == "test-key"
    assert _phone_entry().textvariable.get() == "+15551234567"


@patch("src.ui.settings.sys.platform", "linux")
def test_settings_toggle_shows_and_hides_fields_without_clearing_vars():
    _reset_fakes()

    show_settings_dialog(
        _make_config(),
        tk_module=FakeTkModule(),
        autostart_is_enabled=lambda: False,
        autostart_set_enabled=lambda _enabled: (True, "ok"),
    )

    checkbox = _whatsapp_checkbox()
    assert checkbox.command is not None
    assert _hidden_frames() == []

    checkbox.variable.set(False)
    checkbox.command()
    assert _hidden_frames(), "toggling off should hide the credential fields frame"
    assert _phone_entry().textvariable.get() == "+15551234567"
    assert _api_key_entry().textvariable.get() == "test-key"

    checkbox.variable.set(True)
    checkbox.command()
    assert _hidden_frames() == []
    assert _phone_entry().textvariable.get() == "+15551234567"
    assert _api_key_entry().textvariable.get() == "test-key"
