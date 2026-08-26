"""Tests for alert toast text and engine integration."""

from __future__ import annotations

from unittest.mock import patch

from src.alerts.engine import AlertEngine, AlertState
from src.alerts.sound import MockSoundBackend
from src.alerts.whatsapp import MockWhatsAppClient
from src.config.schema import config_from_dict
from src.ui.alert_toast import alert_toast_background_color, format_alert_toast_text


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
    }
    data.update(overrides)
    return config_from_dict(data)


def test_format_alert_toast_text():
    title, body = format_alert_toast_text(87.4, 70)
    assert title == "CPU/GPU Temperature Alert"
    assert "87.4°C" in body
    assert "70°C" in body


def test_alert_toast_background_color_tiers():
    threshold = 85
    critical = (90, 95)

    assert alert_toast_background_color(86.0, threshold, critical) == "#D97706"
    assert alert_toast_background_color(92.0, threshold, critical) == "#EA580C"
    assert alert_toast_background_color(97.0, threshold, critical) == "#B42318"


def test_alert_toast_background_color_at_boundaries():
    threshold = 85
    critical = (90, 95)

    assert alert_toast_background_color(85.0, threshold, critical) == "#D97706"
    assert alert_toast_background_color(90.0, threshold, critical) == "#EA580C"
    assert alert_toast_background_color(95.0, threshold, critical) == "#B42318"


def test_engine_shows_toast_once_when_alert_starts():
    engine = AlertEngine(_make_config(), MockSoundBackend(), MockWhatsAppClient())
    with patch("src.alerts.engine.show_temperature_alert_toast") as show_toast:
        engine.process_peak(86.0)
        engine.process_peak(87.0)
    assert show_toast.call_count == 1
    show_toast.assert_called_with(86.0, 85, critical_tiers=(90, 95))


def test_engine_shows_toast_again_after_temperature_drops_below_threshold():
    engine = AlertEngine(_make_config(), MockSoundBackend(), MockWhatsAppClient())
    with patch("src.alerts.engine.show_temperature_alert_toast") as show_toast:
        engine.process_peak(86.0)
        engine.process_peak(84.0)
        engine.process_peak(86.0)
    assert show_toast.call_count == 2
    assert engine.state in (AlertState.ALERTING, AlertState.COOLDOWN)
