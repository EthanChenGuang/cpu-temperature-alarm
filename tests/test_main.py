"""WSL-safe unit tests for production entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import sys

from src.paths import app_root, vendor_dir


def test_app_root_dev_mode():
    root = app_root()
    assert (root / "src" / "main.py").exists()
    assert (root / "config" / "config.example.json").exists()


def test_vendor_dir_prefers_internal_bundle(tmp_path, monkeypatch):
    exe_dir = tmp_path / "dist" / "cpu-temp-alert"
    internal_vendor = exe_dir / "_internal" / "vendor" / "LibreHardwareMonitor"
    internal_vendor.mkdir(parents=True)
    (internal_vendor / "LibreHardwareMonitorLib.dll").write_text("stub")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        "src.paths.sys.executable",
        str(exe_dir / "cpu-temp-alert.exe"),
    )

    assert vendor_dir() == internal_vendor


def test_vendor_dir_prefers_meipass_onefile(tmp_path, monkeypatch):
    meipass = tmp_path / "_meipass"
    bundled_vendor = meipass / "vendor" / "LibreHardwareMonitor"
    bundled_vendor.mkdir(parents=True)
    (bundled_vendor / "LibreHardwareMonitorLib.dll").write_text("stub")

    exe_dir = tmp_path / "install"
    exe_dir.mkdir()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)
    monkeypatch.setattr(
        "src.paths.sys.executable",
        str(exe_dir / "cpu-temp-alert.exe"),
    )

    assert vendor_dir() == bundled_vendor


@patch("src.main.TemperatureTrayApp")
@patch("src.main.LhmBridge")
@patch("src.main.load_config")
def test_main_wires_tray_app(mock_load_config, mock_bridge_cls, mock_tray_cls):
    from src.config.schema import config_from_dict
    from src.main import main

    mock_load_config.return_value = config_from_dict(None)
    mock_bridge = MagicMock()
    mock_bridge_cls.return_value = mock_bridge
    mock_app = MagicMock()
    mock_tray_cls.return_value = mock_app

    main()

    mock_bridge.open.assert_called_once()
    mock_tray_cls.assert_called_once()
    mock_app.run.assert_called_once()


@patch("src.main.CallMeBotClient")
@patch("src.main.load_config")
def test_test_whatsapp_idle_skips_send(mock_load_config, mock_client_cls, tmp_path, monkeypatch):
    from src.config.schema import config_from_dict
    from src.main import _test_whatsapp

    mock_load_config.return_value = config_from_dict(
        {
            "threshold_celsius": 85,
            "critical_tiers_celsius": [90, 95],
            "cooldown_seconds": 180,
            "poll_interval_seconds": 3,
            "whatsapp_phone": "+15551234567",
            "callmebot_api_key": "test-key",
            "beep_frequency_hz": 1000,
            "beep_duration_ms": 500,
            "whatsapp_alerts_enabled": False,
        }
    )
    monkeypatch.setattr("src.main.app_root", lambda: tmp_path)

    assert _test_whatsapp() == 1
    mock_client_cls.return_value.send_alert.assert_not_called()
    result = (tmp_path / "whatsapp-test-result.txt").read_text(encoding="utf-8")
    assert "FAIL" in result
    assert "idle" in result.lower()
