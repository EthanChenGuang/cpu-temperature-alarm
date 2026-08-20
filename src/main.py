"""Production entry point — config, telemetry, alerts, and system tray."""

from __future__ import annotations

import logging
import socket
import sys
from datetime import datetime
from pathlib import Path

from src.alerts.sound import WinsoundBackend
from src.alerts.whatsapp import CallMeBotClient
from src.config.loader import load_config
from src.paths import app_root, vendor_dir
from src.telemetry.exceptions import LhmDllNotFoundError
from src.telemetry.lhm_wrapper import LhmBridge
from src.telemetry.sensor_reader import TelemetryPoller
from src.ui.tray import TemperatureTrayApp

__all__ = ["main"]


def _dump_sensors() -> int:
    _configure_logging()
    from src.platform.windows import is_admin

    bridge = LhmBridge(vendor_dir())
    try:
        bridge.open()
    except LhmDllNotFoundError as exc:
        print(str(exc))
        return 1

    poller = TelemetryPoller(bridge)
    readings, peak = poller.run_once()
    out = app_root() / "sensor-dump.txt"
    cpu_package = next((r.value_celsius for r in readings if r.name == "CPU / CPU Package"), None)
    core_max = next((r.value_celsius for r in readings if r.name == "CPU / Core Max"), None)
    gpu_hot = next((r.value_celsius for r in readings if r.name == "GPU / GPU Hot Spot"), None)
    lines = [
        f"admin: {is_admin()}",
        f"peak: {peak}",
        f"cpu_package: {cpu_package}",
        f"core_max: {core_max}",
        f"gpu_hot_spot: {gpu_hot}",
        f"readings: {len(readings)}",
    ]
    for reading in readings:
        lines.append(f"  {reading.name}: {reading.value_celsius:.1f}°C")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0


def _configure_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if getattr(sys, "frozen", False):
        log_path = app_root() / "cpu-temp-alert.log"
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def _test_whatsapp() -> int:
    _configure_logging()
    config = load_config()
    log_path = app_root() / "cpu-temp-alert.log"
    result_path = app_root() / "whatsapp-test-result.txt"

    if not config.whatsapp_alerts_enabled:
        result_path.write_text(
            "FAIL: WhatsApp alerts are idle — enable WhatsApp message in Settings.\n",
            encoding="utf-8",
        )
        return 1

    client = CallMeBotClient(config.whatsapp_phone, config.callmebot_api_key)

    if not client.is_configured():
        result_path.write_text("FAIL: WhatsApp credentials not configured.\n", encoding="utf-8")
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template = config.alert_message_template
    fields = {
        "peak_temp": "99.9",
        "threshold": config.threshold_celsius,
        "hostname": socket.gethostname(),
        "tier": config.threshold_celsius,
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
    ok = client.send_alert(message).ok
    lines = [
        f"configured: True",
        f"send_alert: {ok}",
        f"log_file: {log_path}",
    ]
    result_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if ok else 1


def main() -> None:
    if "--settings" in sys.argv:
        from src.ui.settings_cli import main as settings_main

        raise SystemExit(settings_main())

    if "--logon-delay" in sys.argv:
        import time

        idx = sys.argv.index("--logon-delay")
        if idx + 1 < len(sys.argv):
            try:
                delay_seconds = max(0, min(int(sys.argv[idx + 1]), 120))
                if delay_seconds:
                    time.sleep(delay_seconds)
            except ValueError:
                pass

    if "--test-whatsapp" in sys.argv:
        raise SystemExit(_test_whatsapp())

    if "--dump-sensors" in sys.argv:
        raise SystemExit(_dump_sensors())

    if "--test-toast" in sys.argv:
        from src.ui.alert_toast import show_temperature_alert_toast

        config = load_config()
        show_temperature_alert_toast(99.9, config.threshold_celsius)
        __import__("time").sleep(6)
        raise SystemExit(0)

    _configure_logging()

    from src.platform.lhm_process import warn_if_lhm_gui_running
    from src.platform.single_instance import acquire_single_instance
    from src.platform.windows import is_admin

    if not acquire_single_instance():
        sys.exit(0)

    warn_if_lhm_gui_running()
    if not is_admin():
        logging.getLogger(__name__).warning(
            "Not running as Administrator — GPU sensors work, but CPU temperatures may be missing."
        )

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
