"""Production entry point — config, telemetry, alerts, and system tray."""

from __future__ import annotations

import logging
import sys

from src.alerts.sound import WinsoundBackend
from src.alerts.whatsapp import CallMeBotClient
from src.config.loader import load_config
from src.paths import vendor_dir
from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBridge
from src.ui.tray import TemperatureTrayApp

__all__ = ["main"]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_config()
    bridge = LhmBridge(vendor_dir())
    try:
        bridge.open()
    except LhmDllNotFoundError as exc:
        print(str(exc))
        sys.exit(1)

    app = TemperatureTrayApp(
        config,
        bridge,
        WinsoundBackend(),
        CallMeBotClient(config.whatsapp_phone, config.callmebot_api_key),
    )
    app.run()


if __name__ == "__main__":
    main()
