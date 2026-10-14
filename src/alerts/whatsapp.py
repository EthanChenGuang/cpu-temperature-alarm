"""Injectable WhatsApp clients for CallMeBot alerts."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
PLACEHOLDER_PREFIX = "YOUR_"
_SSL_CONFIGURED = False
DAILY_LIMIT_BACKOFF_SECONDS = 6 * 3600


@dataclass(frozen=True)
class CallMeBotSendResult:
    ok: bool
    rate_limited: bool = False
    daily_limit_reached: bool = False


def _ensure_ssl_bundle() -> None:
    """Point requests/certifi at the bundled CA store inside PyInstaller one-file builds."""
    global _SSL_CONFIGURED
    if _SSL_CONFIGURED:
        return
    _SSL_CONFIGURED = True
    if not getattr(sys, "frozen", False):
        return
    try:
        import os

        import certifi

        bundle = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    except Exception as exc:
        logger.warning("Could not configure SSL certificate bundle: %s", exc)


def callmebot_success(response: requests.Response) -> bool:
    """Return True only when CallMeBot accepted and queued the message."""
    return classify_callmebot_response(response).ok


def classify_callmebot_response(response: requests.Response) -> CallMeBotSendResult:
    """Classify a CallMeBot HTTP response for retry/backoff decisions."""
    body = response.text.strip()
    upper = body.upper()

    if "LIMIT OF 48" in upper or ("LIMIT OF" in upper and "MESSAGE" in upper):
        return CallMeBotSendResult(False, daily_limit_reached=True)

    if response.status_code == 503 or "TOO MANY REQUESTS" in upper:
        return CallMeBotSendResult(False, rate_limited=True)

    if "ERROR" in upper:
        return CallMeBotSendResult(False)

    if response.ok and ("MESSAGE QUEUED" in upper or "MESSAGE SENT" in upper):
        return CallMeBotSendResult(True)

    return CallMeBotSendResult(False)


class WhatsAppClient(Protocol):
    def send_alert(self, message: str) -> CallMeBotSendResult: ...

    def is_configured(self) -> bool: ...


class MockWhatsAppClient:
    """Test double that records sent messages without HTTP."""

    def __init__(self, configured: bool = True) -> None:
        self.sent: list[str] = []
        self._configured = configured

    def send_alert(self, message: str) -> CallMeBotSendResult:
        if not self._configured:
            return CallMeBotSendResult(False)
        self.sent.append(message)
        return CallMeBotSendResult(True)

    def is_configured(self) -> bool:
        return self._configured


class CallMeBotClient:
    """Production CallMeBot HTTP GET client."""

    def __init__(self, phone: str, api_key: str) -> None:
        self._phone = phone.strip() if phone else ""
        self._api_key = api_key.strip() if api_key else ""

    def update_credentials(self, phone: str, api_key: str) -> None:
        self._phone = phone.strip() if phone else ""
        self._api_key = api_key.strip() if api_key else ""

    def is_configured(self) -> bool:
        if not self._phone or not self._api_key:
            return False
        if self._phone.startswith(PLACEHOLDER_PREFIX) or self._api_key.startswith(PLACEHOLDER_PREFIX):
            return False
        if not self._phone.startswith("+"):
            return False
        return True

    def send_alert(self, message: str) -> CallMeBotSendResult:
        if not self.is_configured():
            return CallMeBotSendResult(False)

        _ensure_ssl_bundle()
        url = f"{CALLMEBOT_URL}?phone={quote(self._phone)}&text={quote(message)}&apikey={quote(self._api_key)}"

        try:
            response = requests.get(url, timeout=10)
            result = classify_callmebot_response(response)
            if result.ok:
                logger.info("CallMeBot message queued for %s", self._phone)
                return result
            if result.daily_limit_reached:
                logger.warning(
                    "CallMeBot daily message limit reached (48/day) — WhatsApp alerts paused"
                )
            elif result.rate_limited:
                logger.warning(
                    "CallMeBot rate limit (HTTP %s) — backing off before retry",
                    response.status_code,
                )
            else:
                logger.warning(
                    "CallMeBot rejected message — HTTP %s: %s",
                    response.status_code,
                    response.text[:200],
                )
            return result
        except requests.RequestException as exc:
            logger.warning("CallMeBot request failed: %s", exc)
            return CallMeBotSendResult(False)
