"""WSL-safe unit tests for alert engine, tier escalation, and cooldown."""

from __future__ import annotations

import logging

import pytest

from src.alerts.engine import AlertEngine, AlertState
from src.alerts.sound import MockSoundBackend
from src.alerts.whatsapp import CallMeBotClient, MockWhatsAppClient
from src.config.schema import AppConfig, config_from_dict, validate_config


def _make_config(**overrides) -> AppConfig:
    data = {
        "threshold_celsius": 85,
        "critical_tiers_celsius": [90, 95],
        "cooldown_seconds": 180,
        "poll_interval_seconds": 3,
        "whatsapp_phone": "+15551234567",
        "callmebot_api_key": "test-key",
        "beep_frequency_hz": 1000,
        "beep_duration_ms": 500,
        "alert_message_template": (
            "CPU/GPU ALERT: Peak temperature {peak_temp}°C exceeds threshold "
            "{threshold}°C on {hostname}."
        ),
    }
    data.update(overrides)
    return config_from_dict(data)


def _make_engine(
    config: AppConfig | None = None,
    *,
    clock: list[float] | None = None,
    hostname: str = "test-host",
) -> tuple[AlertEngine, MockSoundBackend, MockWhatsAppClient]:
    cfg = config or _make_config()
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    time_values = clock if clock is not None else [0.0]

    def fake_clock() -> float:
        return time_values[-1]

    engine = AlertEngine(cfg, sound, whatsapp, clock=fake_clock, hostname=hostname)
    return engine, sound, whatsapp


# --- Task 1 tracer ---


def test_alert_tracer_peak_crossing_starts_beep_and_sends_whatsapp():
    engine, sound, whatsapp = _make_engine()

    engine.process_peak(86.0)
    assert sound.is_beeping
    assert len(whatsapp.sent) == 1

    engine.process_peak(80.0)
    assert not sound.is_beeping


# --- Task 2 tier / cooldown ---


def test_tier_escalation_bypasses_cooldown():
    clock = [0.0]
    engine, sound, whatsapp = _make_engine(clock=clock)

    engine.process_peak(86.0)
    assert len(whatsapp.sent) == 1
    assert sound.is_beeping

    clock[0] = 30.0
    engine.process_peak(91.0)
    assert len(whatsapp.sent) == 2
    assert "CRITICAL tier 90°C" in whatsapp.sent[1]

    clock[0] = 60.0
    engine.process_peak(96.0)
    assert len(whatsapp.sent) == 3
    assert "CRITICAL tier 95°C" in whatsapp.sent[2]


def test_same_tier_cooldown_suppresses_duplicate():
    clock = [0.0]
    engine, _sound, whatsapp = _make_engine(clock=clock)

    engine.process_peak(86.0)
    assert len(whatsapp.sent) == 1

    clock[0] = 30.0
    engine.process_peak(86.5)
    assert len(whatsapp.sent) == 1

    clock[0] = 181.0
    engine.process_peak(86.0)
    assert len(whatsapp.sent) == 2


# --- Task 3 remaining coverage ---


def test_peak_none_no_alert():
    engine, sound, whatsapp = _make_engine()

    engine.process_peak(90.0)
    assert sound.is_beeping

    engine.process_peak(None)
    assert not sound.is_beeping
    assert len(whatsapp.sent) == 1
    assert engine.state is AlertState.NORMAL


def test_beep_stops_when_below_threshold():
    engine, sound, whatsapp = _make_engine()

    engine.process_peak(88.0)
    assert sound.is_beeping
    assert sound.start_count == 1

    engine.process_peak(84.0)
    assert not sound.is_beeping
    assert sound.stop_count >= 1
    assert engine.state is AlertState.NORMAL


def test_first_breach_sends_whatsapp():
    engine, sound, whatsapp = _make_engine(hostname="my-pc")

    engine.process_peak(80.0)
    assert not sound.is_beeping
    assert len(whatsapp.sent) == 0

    engine.process_peak(85.0)
    assert sound.is_beeping
    assert len(whatsapp.sent) == 1
    assert "85.0" in whatsapp.sent[0]
    assert "my-pc" in whatsapp.sent[0]


def test_whatsapp_skipped_when_unconfigured(caplog):
    config = _make_config(
        whatsapp_phone="+15551234567",
        callmebot_api_key="YOUR_CALLMEBOT_API_KEY",
    )
    sound = MockSoundBackend()
    whatsapp = CallMeBotClient(config.whatsapp_phone, config.callmebot_api_key)
    engine = AlertEngine(config, sound, whatsapp, hostname="test-host")

    with caplog.at_level(logging.WARNING):
        engine.process_peak(90.0)
        engine.process_peak(92.0)

    assert sound.is_beeping
    assert not whatsapp.is_configured()
    assert sum("WhatsApp alerts skipped" in r.message for r in caplog.records) == 1


def test_config_validation_rejects_unsorted_tiers():
    with pytest.raises(ValueError, match="sorted ascending"):
        validate_config(
            {
                "threshold_celsius": 85,
                "critical_tiers_celsius": [95, 90],
                "cooldown_seconds": 180,
                "poll_interval_seconds": 3,
                "beep_frequency_hz": 1000,
                "beep_duration_ms": 500,
                "alert_message_template": "alert {peak_temp} {threshold} {hostname}",
            }
        )


def test_alert_state_cooldown_while_over_threshold():
    clock = [0.0]
    engine, sound, whatsapp = _make_engine(clock=clock)

    engine.process_peak(86.0)
    assert engine.state is AlertState.ALERTING
    assert sound.is_beeping

    clock[0] = 10.0
    engine.process_peak(86.0)
    assert engine.state is AlertState.COOLDOWN
    assert sound.is_beeping
    assert len(whatsapp.sent) == 1
