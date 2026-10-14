"""Tests for Windows autostart helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.platform.autostart import (
    DEFAULT_TASK_NAME,
    STARTUP_SHORTCUT_NAME,
    disable_autostart,
    enable_autostart,
    is_autostart_enabled,
    set_autostart,
    startup_shortcut_path,
)


@pytest.mark.skipif(sys.platform == "win32", reason="Uses mocked subprocess on non-Windows")
def test_is_autostart_enabled_false_on_non_windows():
    assert is_autostart_enabled() is False


@pytest.mark.skipif(sys.platform == "win32", reason="Uses mocked subprocess on non-Windows")
def test_enable_autostart_requires_windows():
    ok, message = enable_autostart()
    assert ok is False
    assert "Windows" in message


@patch("src.platform.autostart.startup_shortcut_path")
@patch("src.platform.autostart.hidden_subprocess_kwargs", return_value={"creationflags": 0})
@patch("src.platform.autostart.sys.platform", "win32")
@patch("src.platform.autostart.subprocess.run")
def test_is_autostart_enabled_true_when_shortcut_exists(mock_run, _hidden, mock_shortcut_path):
    mock_shortcut_path.return_value = Path("/tmp/startup/CPU Temp Alert.lnk")
    with patch.object(Path, "is_file", return_value=True):
        assert is_autostart_enabled(DEFAULT_TASK_NAME) is True
    mock_run.assert_not_called()


@patch("src.platform.autostart.startup_shortcut_path")
@patch("src.platform.autostart.hidden_subprocess_kwargs", return_value={"creationflags": 0})
@patch("src.platform.autostart.sys.platform", "win32")
@patch("src.platform.autostart.subprocess.run")
def test_is_autostart_enabled_falls_back_to_scheduled_task(mock_run, _hidden, mock_shortcut_path):
    mock_shortcut_path.return_value = Path("/tmp/startup/CPU Temp Alert.lnk")
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    with patch.object(Path, "is_file", return_value=False):
        assert is_autostart_enabled(DEFAULT_TASK_NAME) is True

    assert "Get-ScheduledTask" in mock_run.call_args[0][0][-1]


@patch("src.platform.autostart._remove_legacy_scheduled_task")
@patch("src.platform.autostart.hidden_subprocess_kwargs", return_value={"creationflags": 0})
@patch("src.platform.autostart.sys.platform", "win32")
@patch("src.platform.autostart.Path.exists", return_value=True)
@patch("src.platform.autostart.autostart_launch_spec")
@patch("src.platform.autostart.subprocess.run")
def test_enable_autostart_creates_startup_shortcut(
    mock_run, mock_spec, _mock_exists, _hidden, mock_remove_legacy
):
    mock_spec.return_value = (r"D:\apps\cpu-temp-alert-v6.9.exe", "--logon-delay 30", Path(r"D:\apps"))
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    ok, message = enable_autostart()

    assert ok is True
    assert "Start with Windows enabled" in message
    script = mock_run.call_args[0][0][-1]
    assert "WScript.Shell" in script
    assert STARTUP_SHORTCUT_NAME in script
    assert "0x20" in script
    assert "--logon-delay 30" in script
    mock_remove_legacy.assert_called_once()


@patch("src.platform.autostart._remove_legacy_scheduled_task")
@patch("src.platform.autostart.startup_shortcut_path")
@patch("src.platform.autostart.sys.platform", "win32")
def test_disable_autostart_removes_shortcut(mock_shortcut_path, _remove_legacy, tmp_path):
    shortcut = tmp_path / STARTUP_SHORTCUT_NAME
    shortcut.write_text("stub", encoding="utf-8")
    mock_shortcut_path.return_value = shortcut

    ok, message = disable_autostart()

    assert ok is True
    assert "Start with Windows disabled" in message
    assert not shortcut.exists()


@patch("src.platform.autostart.enable_autostart", return_value=(True, "enabled"))
def test_set_autostart_enable(mock_enable):
    assert set_autostart(True) == (True, "enabled")
    mock_enable.assert_called_once()


@patch("src.platform.autostart.disable_autostart", return_value=(True, "disabled"))
def test_set_autostart_disable(mock_disable):
    assert set_autostart(False) == (True, "disabled")
    mock_disable.assert_called_once()
