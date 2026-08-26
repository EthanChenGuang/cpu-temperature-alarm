---
quick_id: 260826-dla
status: complete
commit: c909f1b
---

# Summary: Temperature-based alert toast colors

## Done

- Added `alert_toast_background_color()` with three-tier severity ramp aligned to config tiers
- Toast background now uses dynamic color instead of fixed `#b42318`
- Engine passes `critical_tiers_celsius` when showing toast
- Unit tests cover tier boundaries (85 / 90 / 95°C)

## Color tiers (default config)

| Temperature | Severity | Color |
|-------------|----------|-------|
| 85–89°C | Warning | Amber `#D97706` |
| 90–94°C | High | Orange `#EA580C` |
| ≥95°C | Critical | Deep red `#B42318` |

## Verification

`pytest tests/test_alert_toast.py -v` — 5 passed
