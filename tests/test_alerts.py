"""WSL-safe unit tests for alert engine, tier escalation, and cooldown."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

import pytest

from src.alerts.engine import AlertEngine, AlertState
from src.alerts.sound import MockSoundBackend
from src.alerts.whatsapp import CallMeBotClient, CallMeBotSendResult, MockWhatsAppClient, callmebot_success, classify_callmebot_response
from src.config.schema import AppConfig, config_from_dict, config_to_dict, validate_config


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
    wall_clock: Callable[[], datetime] | None = None,
    hostname: str = "test-host",
    **config_overrides,
) -> tuple[AlertEngine, MockSoundBackend, MockWhatsAppClient]:
    cfg = config or _make_config(**config_overrides)
    sound = MockSoundBackend()
    whatsapp = MockWhatsAppClient()
    time_values = clock if clock is not None else [0.0]
    fixed_wall = wall_clock

    def fake_clock() -> float:
        return time_values[-1]

    def fake_wall_clock() -> datetime:
        return fixed_wall() if fixed_wall is not None else datetime.now()

    engine = AlertEngine(
        cfg,
        sound,
        whatsapp,
        clock=fake_clock,
        wall_clock=fake_wall_clock,
        hostname=hostname,
    )
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


def test_alert_message_includes_timestamp():
    fixed = datetime(2026, 8, 19, 15, 25, 30)
    engine, _sound, whatsapp = _make_engine(
        config=_make_config(
            alert_message_template=(
                "CPU/GPU ALERT: Peak temperature {peak_temp}°C exceeds threshold "
                "{threshold}°C on {hostname}. [{timestamp}]"
            )
        ),
        wall_clock=lambda: fixed,
    )

    engine.process_peak(86.0)
    assert len(whatsapp.sent) == 1
    assert whatsapp.sent[0].endswith("[2026-08-19 15:25:30]")


def test_alert_message_appends_timestamp_for_legacy_template():
    fixed = datetime(2026, 8, 19, 15, 25, 30)
    engine, _sound, whatsapp = _make_engine(
        config=_make_config(
            alert_message_template=(
                "CPU/GPU ALERT: Peak temperature {peak_temp}°C exceeds threshold "
                "{threshold}°C on {hostname}."
            )
        ),
        wall_clock=lambda: fixed,
    )

    engine.process_peak(86.0)
    assert whatsapp.sent[0].endswith("[2026-08-19 15:25:30]")


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


class _FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text
        self.ok = 200 <= status_code < 400


def test_callmebot_success_accepts_queued_message():
    response = _FakeResponse(200, "<b>Message queued.</b> You will receive it in a few seconds.")
    assert callmebot_success(response) is True


def test_callmebot_success_rejects_error_body():
    response = _FakeResponse(201, "ERROR: apikey can not be empty")
    assert callmebot_success(response) is False


def test_callmebot_classifies_daily_limit():
    response = _FakeResponse(
        209,
        "ERROR: There is currently a limit of 48 messages per day",
    )
    result = classify_callmebot_response(response)
    assert result.ok is False
    assert result.daily_limit_reached is True


def test_callmebot_classifies_rate_limit():
    response = _FakeResponse(503, "<h1>Oops! Too many requests...</h1>")
    result = classify_callmebot_response(response)
    assert result.ok is False
    assert result.rate_limited is True


class _FailingWhatsAppClient:
    def __init__(self) -> None:
        self.attempts = 0

    def send_alert(self, message: str) -> CallMeBotSendResult:
        self.attempts += 1
        return CallMeBotSendResult(False, rate_limited=True)

    def is_configured(self) -> bool:
        return True


def test_whatsapp_failure_still_respects_cooldown():
    clock = [0.0]
    failing = _FailingWhatsAppClient()
    engine = AlertEngine(
        _make_config(),
        MockSoundBackend(),
        failing,
        clock=lambda: clock[0],
    )

    engine.process_peak(86.0)
    assert failing.attempts == 1

    clock[0] = 30.0
    engine.process_peak(86.0)
    assert failing.attempts == 1

    clock[0] = 181.0
    engine.process_peak(86.0)
    assert failing.attempts == 2


def test_whatsapp_daily_limit_pauses_all_tiers():
    clock = [0.0]

    class _DailyLimitClient:
        def __init__(self) -> None:
            self.attempts = 0

        def send_alert(self, message: str) -> CallMeBotSendResult:
            self.attempts += 1
            return CallMeBotSendResult(False, daily_limit_reached=True)

        def is_configured(self) -> bool:
            return True

    client = _DailyLimitClient()
    engine = AlertEngine(
        _make_config(),
        MockSoundBackend(),
        client,
        clock=lambda: clock[0],
    )

    engine.process_peak(86.0)
    assert client.attempts == 1

    clock[0] = 5000.0
    engine.process_peak(96.0)
    assert client.attempts == 1


def test_warning_tier_uses_standard_beep_pattern():
    engine, sound, _whatsapp = _make_engine()

    engine.process_peak(86.0)

    assert sound.is_beeping
    assert sound.last_pattern is not None
    assert sound.last_pattern.burst_count == 2
    assert sound.last_pattern.interval_seconds == 10.0


def test_critical_tier_uses_urgent_beep_pattern():
    engine, sound, _whatsapp = _make_engine()

    engine.process_peak(91.0)

    assert sound.is_beeping
    assert sound.last_pattern is not None
    assert sound.last_pattern.burst_count == 3
    assert sound.last_pattern.interval_seconds == 30.0


def test_sound_alerts_disabled_in_config_suppresses_beep():
    engine, sound, whatsapp = _make_engine(sound_alerts_enabled=False)

    engine.process_peak(86.0)
    assert not sound.is_beeping
    assert engine.state is AlertState.ALERTING
    assert len(whatsapp.sent) == 1


def test_whatsapp_alerts_enabled_defaults_true_when_omitted():
    config = config_from_dict(
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
    assert config.whatsapp_alerts_enabled is True
    serialized = config_to_dict(config)
    assert serialized["whatsapp_alerts_enabled"] is True


def test_whatsapp_alerts_disabled_skips_send():
    engine, sound, whatsapp = _make_engine(whatsapp_alerts_enabled=False)

    engine.process_peak(86.0)
    assert sound.is_beeping
    assert engine.state is AlertState.ALERTING
    assert len(whatsapp.sent) == 0


def test_mute_suppresses_beep_but_keeps_alert_state():
    engine, sound, whatsapp = _make_engine()

    engine.process_peak(86.0)
    assert sound.is_beeping
    assert engine.state is AlertState.ALERTING

    engine.mute(900)
    assert engine.is_muted
    assert not sound.is_beeping

    engine.process_peak(87.0)
    assert not sound.is_beeping
    assert engine.state is AlertState.COOLDOWN
    assert len(whatsapp.sent) == 1
