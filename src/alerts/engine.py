"""Poll-driven alert state machine with tier escalation and per-tier cooldown."""

from __future__ import annotations

import logging
import socket
from enum import Enum
from typing import Callable

from src.alerts.sound import SoundBackend
from src.alerts.whatsapp import WhatsAppClient
from src.config.schema import AppConfig

logger = logging.getLogger(__name__)

__all__ = ["AlertEngine", "AlertState"]


class AlertState(str, Enum):
    NORMAL = "normal"
    ALERTING = "alerting"
    COOLDOWN = "cooldown"


class AlertEngine:
    """Process peak temperature each poll cycle; drive sound and WhatsApp backends."""

    def __init__(
        self,
        config: AppConfig,
        sound: SoundBackend,
        whatsapp: WhatsAppClient,
        *,
        clock: Callable[[], float] | None = None,
        hostname: str | None = None,
    ) -> None:
        self._config = config
        self._sound = sound
        self._whatsapp = whatsapp
        self._clock = clock if clock is not None else __import__("time").monotonic
        self._hostname = hostname if hostname is not None else socket.gethostname()
        self._state = AlertState.NORMAL
        self._last_sent_monotonic: dict[int, float] = {}
        self._warned_unconfigured = False

    @property
    def state(self) -> AlertState:
        return self._state

    def process_peak(self, peak_temp: float | None) -> None:
        if peak_temp is None:
            self._sound.stop_beep()
            self._state = AlertState.NORMAL
            return

        threshold = self._config.threshold_celsius
        if peak_temp < threshold:
            self._sound.stop_beep()
            self._state = AlertState.NORMAL
            return

        self._sound.start_beep(self._config.beep_frequency_hz, self._config.beep_duration_ms)

        current_tier = self._current_tier(peak_temp)
        sent_this_cycle = False
        if self._should_send_whatsapp(current_tier):
            if self._whatsapp.is_configured():
                message = self._format_message(peak_temp, current_tier)
                if self._whatsapp.send_alert(message):
                    self._last_sent_monotonic[current_tier] = self._clock()
                    sent_this_cycle = True
            else:
                self._warn_unconfigured_once()

        if not sent_this_cycle and self._is_tier_in_cooldown(current_tier):
            self._state = AlertState.COOLDOWN
        else:
            self._state = AlertState.ALERTING

    def _current_tier(self, peak_temp: float) -> int:
        crossed = [t for t in self._config.all_tiers if peak_temp >= t]
        return max(crossed)

    def _is_tier_in_cooldown(self, tier: int) -> bool:
        last_sent = self._last_sent_monotonic.get(tier)
        if last_sent is None:
            return False
        return (self._clock() - last_sent) < self._config.cooldown_seconds

    def _should_send_whatsapp(self, current_tier: int) -> bool:
        if not self._is_tier_in_cooldown(current_tier):
            return True
        return False

    def _format_message(self, peak_temp: float, current_tier: int) -> str:
        message = self._config.alert_message_template.format(
            peak_temp=f"{peak_temp:.1f}",
            threshold=self._config.threshold_celsius,
            hostname=self._hostname,
            tier=current_tier,
        )
        if current_tier in self._config.critical_tiers_celsius:
            message = f"CRITICAL tier {current_tier}°C — {message}"
        return message

    def _warn_unconfigured_once(self) -> None:
        if self._warned_unconfigured:
            return
        logger.warning(
            "WhatsApp alerts skipped — configure whatsapp_phone and callmebot_api_key in config/config.json"
        )
        self._warned_unconfigured = True
