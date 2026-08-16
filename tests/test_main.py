"""WSL-safe unit tests for production entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.paths import app_root


def test_app_root_dev_mode():
    root = app_root()
    assert (root / "src" / "main.py").exists()
    assert (root / "config" / "config.example.json").exists()


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
