"""Application configuration schema and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_THRESHOLD_CELSIUS = 85
DEFAULT_CRITICAL_TIERS = (90, 95)
DEFAULT_COOLDOWN_SECONDS = 180
DEFAULT_POLL_INTERVAL_SECONDS = 3
DEFAULT_BEEP_FREQUENCY_HZ = 1000
DEFAULT_BEEP_DURATION_MS = 500
DEFAULT_WHATSAPP_PHONE = "+1234567890"
DEFAULT_CALLMEBOT_API_KEY = "YOUR_CALLMEBOT_API_KEY"
DEFAULT_ALERT_MESSAGE_TEMPLATE = (
    "CPU/GPU ALERT: Peak temperature {peak_temp}°C exceeds threshold {threshold}°C on {hostname}."
)


@dataclass(frozen=True)
class AppConfig:
    threshold_celsius: int = DEFAULT_THRESHOLD_CELSIUS
    critical_tiers_celsius: tuple[int, ...] = DEFAULT_CRITICAL_TIERS
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS
    whatsapp_phone: str = DEFAULT_WHATSAPP_PHONE
    callmebot_api_key: str = DEFAULT_CALLMEBOT_API_KEY
    beep_frequency_hz: int = DEFAULT_BEEP_FREQUENCY_HZ
    beep_duration_ms: int = DEFAULT_BEEP_DURATION_MS
    alert_message_template: str = DEFAULT_ALERT_MESSAGE_TEMPLATE

    @property
    def all_tiers(self) -> tuple[int, ...]:
        tiers = {self.threshold_celsius, *self.critical_tiers_celsius}
        return tuple(sorted(tiers))


def _default_config_dict() -> dict[str, Any]:
    return {
        "threshold_celsius": DEFAULT_THRESHOLD_CELSIUS,
        "critical_tiers_celsius": list(DEFAULT_CRITICAL_TIERS),
        "cooldown_seconds": DEFAULT_COOLDOWN_SECONDS,
        "poll_interval_seconds": DEFAULT_POLL_INTERVAL_SECONDS,
        "whatsapp_phone": DEFAULT_WHATSAPP_PHONE,
        "callmebot_api_key": DEFAULT_CALLMEBOT_API_KEY,
        "beep_frequency_hz": DEFAULT_BEEP_FREQUENCY_HZ,
        "beep_duration_ms": DEFAULT_BEEP_DURATION_MS,
        "alert_message_template": DEFAULT_ALERT_MESSAGE_TEMPLATE,
    }


def config_from_dict(data: dict[str, Any] | None) -> AppConfig:
    """Build AppConfig from a dict, filling missing keys from defaults."""
    merged = _default_config_dict()
    if data:
        merged.update(data)
    validate_config(merged)
    tiers = merged["critical_tiers_celsius"]
    return AppConfig(
        threshold_celsius=int(merged["threshold_celsius"]),
        critical_tiers_celsius=tuple(int(t) for t in tiers),
        cooldown_seconds=int(merged["cooldown_seconds"]),
        poll_interval_seconds=int(merged["poll_interval_seconds"]),
        whatsapp_phone=str(merged.get("whatsapp_phone", DEFAULT_WHATSAPP_PHONE)),
        callmebot_api_key=str(merged.get("callmebot_api_key", DEFAULT_CALLMEBOT_API_KEY)),
        beep_frequency_hz=int(merged["beep_frequency_hz"]),
        beep_duration_ms=int(merged["beep_duration_ms"]),
        alert_message_template=str(merged["alert_message_template"]),
    )


def validate_config(data: dict[str, Any]) -> None:
    """Validate config ranges per D-16."""
    threshold = int(data["threshold_celsius"])
    if not 1 <= threshold <= 150:
        raise ValueError(f"threshold_celsius must be 1–150, got {threshold}")

    tiers_raw = data["critical_tiers_celsius"]
    if not isinstance(tiers_raw, list) or not tiers_raw:
        raise ValueError("critical_tiers_celsius must be a non-empty list")

    tiers = [int(t) for t in tiers_raw]
    if len(tiers) != len(set(tiers)):
        raise ValueError("critical_tiers_celsius must contain unique values")
    if tiers != sorted(tiers):
        raise ValueError("critical_tiers_celsius must be sorted ascending")

    cooldown = int(data["cooldown_seconds"])
    if cooldown < 30:
        raise ValueError(f"cooldown_seconds must be >= 30, got {cooldown}")

    beep_hz = int(data["beep_frequency_hz"])
    if not 200 <= beep_hz <= 5000:
        raise ValueError(f"beep_frequency_hz must be 200–5000, got {beep_hz}")

    beep_ms = int(data["beep_duration_ms"])
    if not 100 <= beep_ms <= 2000:
        raise ValueError(f"beep_duration_ms must be 100–2000, got {beep_ms}")

    phone = str(data.get("whatsapp_phone", ""))
    if phone and not phone.startswith("+"):
        raise ValueError("whatsapp_phone must be E.164 format starting with +")
