"""Manual verification harness: telemetry poll → alert engine loop (D-18)."""

from __future__ import annotations

import logging
import sys
import time

from src.alerts.engine import AlertEngine
from src.alerts.sound import WinsoundBackend
from src.alerts.whatsapp import CallMeBotClient
from src.config.loader import load_config
from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBridge
from src.telemetry.sensor_reader import TelemetryPoller

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_config()
    bridge = LhmBridge()
    try:
        bridge.open()
    except LhmDllNotFoundError as exc:
        print(str(exc))
        sys.exit(1)

    sound = WinsoundBackend()
    whatsapp = CallMeBotClient(config.whatsapp_phone, config.callmebot_api_key)
    engine = AlertEngine(config, sound, whatsapp)
    poller = TelemetryPoller(bridge, config.poll_interval_seconds)

    print(
        f"Alert harness running (threshold={config.threshold_celsius}°C, "
        f"poll={config.poll_interval_seconds}s). Ctrl+C to stop."
    )

    try:
        while True:
            _readings, peak = poller.run_once()
            if peak is not None:
                print(f"Peak: {peak}°C — alert state: {engine.state.value}")
            else:
                print(f"Peak: unknown — alert state: {engine.state.value}")
            engine.process_peak(peak)
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        print("\nStopping alert harness...")
        sound.stop_beep()


if __name__ == "__main__":
    main()
