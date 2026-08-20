"""Poll-driven alert state machine with tier escalation and per-tier cooldown."""

from __future__ import annotations

import logging
import socket
from datetime import datetime
from enum import Enum
from typing import Callable

from src.alerts.sound import BeepPattern, SoundBackend
from src.alerts.whatsapp import WhatsAppClient
from src.alerts.whatsapp import CallMeBotSendResult, DAILY_LIMIT_BACKOFF_SECONDS
from src.config.schema import AppConfig
from src.ui.alert_toast import show_temperature_alert_toast

logger = logging.getLogger(__name__)

ALERT_CLEAR_HYSTERESIS_C = 1.0

__all__ = ["AlertEngine", "AlertState", "ALERT_CLEAR_HYSTERESIS_C"]


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
        wall_clock: Callable[[], datetime] | None = None,
        hostname: str | None = None,
    ) -> None:
        self._config = config
        self._sound = sound
        self._whatsapp = whatsapp
        self._clock = clock if clock is not None else __import__("time").monotonic
        self._wall_clock = wall_clock if wall_clock is not None else datetime.now
        self._hostname = hostname if hostname is not None else socket.gethostname()
        self._state = AlertState.NORMAL
        self._last_sent_monotonic: dict[int, float] = {}
        self._warned_unconfigured = False
        self._muted_until_monotonic: float | None = None
        self._cooldown_notice_tier: int | None = None
        self._whatsapp_blocked_until_monotonic: float | None = None
        self._daily_limit_logged = False
        self._beep_active_logged = False

    def update_config(self, config: AppConfig) -> None:
        """Apply new settings without resetting cooldown or mute state."""
        self._config = config

    @property
    def state(self) -> AlertState:
        return self._state

    @property
    def is_muted(self) -> bool:
        if self._muted_until_monotonic is None:
            return False
        if self._clock() >= self._muted_until_monotonic:
            self._muted_until_monotonic = None
            return False
        return True

    def mute(self, duration_seconds: int | None = None) -> None:
        seconds = duration_seconds if duration_seconds is not None else self._config.mute_duration_seconds
        self._muted_until_monotonic = self._clock() + seconds
        self._sound.stop_beep()
        logger.info("Local alert sound muted for %s seconds", seconds)

    def process_peak(self, peak_temp: float | None) -> None:
        if peak_temp is None:
            self._sound.stop_beep()
            self._state = AlertState.NORMAL
            self._cooldown_notice_tier = None
            self._beep_active_logged = False
            return

        threshold = self._config.threshold_celsius

        if peak_temp < threshold:
            if self._state is not AlertState.NORMAL:
                logger.info(
                    "Temperature back to normal: peak=%.1f°C (below threshold %d°C)",
                    peak_temp,
                    threshold,
                )
            self._sound.stop_beep()
            self._state = AlertState.NORMAL
            self._cooldown_notice_tier = None
            self._beep_active_logged = False
            return

        current_tier = self._current_tier(peak_temp)
        if self._state is AlertState.NORMAL:
            logger.info(
                "Temperature alert: peak=%.1f°C >= threshold=%d°C (sound=%s, muted=%s)",
                peak_temp,
                threshold,
                self._config.sound_alerts_enabled,
                self.is_muted,
            )
            show_temperature_alert_toast(peak_temp, threshold)

        if self._config.sound_alerts_enabled and not self.is_muted:
            pattern = self._beep_pattern_for_tier(current_tier)
            self._sound.start_beep(
                self._config.beep_frequency_hz,
                self._config.beep_duration_ms,
                pattern=pattern,
            )
            if not self._beep_active_logged:
                logger.info(
                    "Local beep active: %d×%dms every %.0fs (muted=%s)",
                    pattern.burst_count,
                    self._config.beep_duration_ms,
                    pattern.interval_seconds,
                    self.is_muted,
                )
                self._beep_active_logged = True
        else:
            self._sound.stop_beep()
            self._beep_active_logged = False

        sent_this_cycle = False
        if self._config.whatsapp_alerts_enabled:
            if self._should_send_whatsapp(current_tier):
                if self._whatsapp.is_configured():
                    message = self._format_message(peak_temp, current_tier)
                    result = self._whatsapp.send_alert(message)
                    self._record_whatsapp_attempt(current_tier)
                    if result.ok:
                        sent_this_cycle = True
                        self._cooldown_notice_tier = None
                        logger.info(
                            "WhatsApp alert sent: peak=%.1f°C tier=%d°C",
                            peak_temp,
                            current_tier,
                        )
                    elif result.daily_limit_reached:
                        self._whatsapp_blocked_until_monotonic = (
                            self._clock() + DAILY_LIMIT_BACKOFF_SECONDS
                        )
                        if not self._daily_limit_logged:
                            logger.warning(
                                "WhatsApp paused for %dh — CallMeBot free tier allows 48 messages/day",
                                DAILY_LIMIT_BACKOFF_SECONDS // 3600,
                            )
                            self._daily_limit_logged = True
                    else:
                        logger.warning(
                            "WhatsApp alert failed: peak=%.1f°C tier=%d°C — retry after cooldown",
                            peak_temp,
                            current_tier,
                        )
                else:
                    self._warn_unconfigured_once()
            elif self._cooldown_notice_tier != current_tier:
                if self._is_whatsapp_globally_blocked():
                    remaining = int(self._whatsapp_blocked_until_monotonic - self._clock())  # type: ignore[operator]
                    logger.info(
                        "WhatsApp paused (CallMeBot daily limit) — ~%ds remaining",
                        max(0, remaining),
                    )
                else:
                    remaining = self._config.cooldown_seconds - int(
                        self._clock() - (self._last_sent_monotonic.get(current_tier) or self._clock())
                    )
                    logger.info(
                        "WhatsApp cooldown active for tier %d°C (~%ds until next message)",
                        current_tier,
                        max(0, remaining),
                    )
                self._cooldown_notice_tier = current_tier

        if self._config.whatsapp_alerts_enabled and not sent_this_cycle and self._is_tier_in_cooldown(current_tier):
            self._state = AlertState.COOLDOWN
        else:
            self._state = AlertState.ALERTING

    def _beep_pattern_for_tier(self, tier: int) -> BeepPattern:
        if tier in self._config.critical_tiers_celsius:
            return BeepPattern(
                burst_count=self._config.critical_beep_burst_count,
                burst_gap_ms=self._config.beep_burst_gap_ms,
                interval_seconds=float(self._config.critical_beep_interval_seconds),
            )
        return BeepPattern(
            burst_count=self._config.beep_burst_count,
            burst_gap_ms=self._config.beep_burst_gap_ms,
            interval_seconds=float(self._config.beep_interval_seconds),
        )

    def _current_tier(self, peak_temp: float) -> int:
        crossed = [t for t in self._config.all_tiers if peak_temp >= t]
        return max(crossed)

    def _is_tier_in_cooldown(self, tier: int) -> bool:
        last_sent = self._last_sent_monotonic.get(tier)
        if last_sent is None:
            return False
        return (self._clock() - last_sent) < self._config.cooldown_seconds

    def _record_whatsapp_attempt(self, tier: int) -> None:
        """Apply cooldown after any send attempt so failures do not spam CallMeBot."""
        self._last_sent_monotonic[tier] = self._clock()

    def _is_whatsapp_globally_blocked(self) -> bool:
        if self._whatsapp_blocked_until_monotonic is None:
            return False
        if self._clock() >= self._whatsapp_blocked_until_monotonic:
            self._whatsapp_blocked_until_monotonic = None
            self._daily_limit_logged = False
            return False
        return True

    def _should_send_whatsapp(self, current_tier: int) -> bool:
        if self._is_whatsapp_globally_blocked():
            return False
        if not self._is_tier_in_cooldown(current_tier):
            return True
        return False

    def _format_message(self, peak_temp: float, current_tier: int) -> str:
        timestamp = self._wall_clock().strftime("%Y-%m-%d %H:%M:%S")
        template = self._config.alert_message_template
        fields = {
            "peak_temp": f"{peak_temp:.1f}",
            "threshold": self._config.threshold_celsius,
            "hostname": self._hostname,
            "tier": current_tier,
            "timestamp": timestamp,
        }
        if "{timestamp}" in template:
            message = template.format(**fields)
        else:
            message = template.format(
                peak_temp=fields["peak_temp"],
                threshold=fields["threshold"],
                hostname=fields["hostname"],
                tier=fields["tier"],
            )
            message = f"{message} [{timestamp}]"
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
