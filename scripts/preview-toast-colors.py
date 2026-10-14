"""Preview alert toast colors at each severity tier (Windows only)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

if sys.platform != "win32":
    print("Toast preview requires Windows (tkinter popup).")
    raise SystemExit(1)

# Import alert_toast directly so this script works without pulling in tray deps.
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.ui.alert_toast import alert_toast_background_color, show_temperature_alert_toast

THRESHOLD = 85
CRITICAL_TIERS = (90, 95)
PREVIEW_TEMPS = [
    (86.0, "Warning (amber)"),
    (92.0, "High (orange)"),
    (97.0, "Critical (deep red)"),
]
DISPLAY_SECONDS = 4.0
GAP_SECONDS = 0.8


def main() -> int:
    print("Alert toast color preview — close each popup or wait for auto-dismiss.\n")
    for peak_temp, label in PREVIEW_TEMPS:
        color = alert_toast_background_color(peak_temp, THRESHOLD, CRITICAL_TIERS)
        print(f"  {peak_temp:.1f}°C — {label} — {color}")
        show_temperature_alert_toast(
            peak_temp,
            THRESHOLD,
            critical_tiers=CRITICAL_TIERS,
            duration_seconds=DISPLAY_SECONDS,
        )
        time.sleep(DISPLAY_SECONDS + GAP_SECONDS)

    print("\nPreview complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
