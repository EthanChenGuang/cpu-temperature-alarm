---
quick_id: 260826-dla
status: planned
---

# Quick Plan: Temperature-based alert toast colors

## Goal

Alert toast background should intensify from amber → orange → deep red as peak temperature rises through configured tiers.

## Color tiers (best-practice severity ramp)

| Severity | Condition (default config) | Color | Hex |
|----------|---------------------------|-------|-----|
| Warning  | threshold ≤ peak < tier₁  | Amber | `#D97706` |
| High     | tier₁ ≤ peak < tier₂      | Orange | `#EA580C` |
| Critical | peak ≥ highest tier       | Deep red | `#B42318` |

Uses `threshold_celsius` and `critical_tiers_celsius` from config — same tier model as alert engine.

## Tasks

### Task 1: Add color resolver and wire into toast

- **files:** `src/ui/alert_toast.py`, `src/alerts/engine.py`, `src/main.py`
- **action:** Add `alert_toast_background_color(peak_temp, threshold, critical_tiers)`; pass color through `_run_toast`; engine passes `critical_tiers_celsius` when showing toast
- **verify:** `pytest tests/test_alert_toast.py -v`
- **done:** Toast uses tier-based background color

### Task 2: Add unit tests for color tiers

- **files:** `tests/test_alert_toast.py`
- **action:** Test color resolver at each severity boundary (85, 90, 95 with default tiers)
- **verify:** `pytest tests/test_alert_toast.py -v`
- **done:** All tier boundaries covered
