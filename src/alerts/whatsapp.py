"""Injectable WhatsApp clients for CallMeBot alerts."""

from __future__ import annotations

import logging
from typing import Protocol
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
PLACEHOLDER_PREFIX = "YOUR_"


class WhatsAppClient(Protocol):
    def send_alert(self, message: str) -> bool: ...

    def is_configured(self) -> bool: ...


class MockWhatsAppClient:
    """Test double that records sent messages without HTTP."""

    def __init__(self, configured: bool = True) -> None:
        self.sent: list[str] = []
        self._configured = configured

    def send_alert(self, message: str) -> bool:
        if not self._configured:
            return False
        self.sent.append(message)
        return True

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

    def send_alert(self, message: str) -> bool:
        if not self.is_configured():
            return False

        url = f"{CALLMEBOT_URL}?phone={quote(self._phone)}&text={quote(message)}&apikey={quote(self._api_key)}"

        try:
            response = requests.get(url, timeout=10)
            if not response.ok:
                logger.warning(
                    "CallMeBot HTTP %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                return False
            return True
        except requests.RequestException as exc:
            logger.warning("CallMeBot request failed: %s", exc)
            return False
