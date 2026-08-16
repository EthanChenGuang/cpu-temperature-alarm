---
phase: 03-tray-ui-settings
plan: 01
subsystem: ui
tags: [pystray, pillow, tkinter, tray, settings]

requires:
  - phase: 02-alert-engine
    provides: AlertEngine, config loader, sound/WhatsApp backends
  - phase: 01-telemetry-foundation
    provides: TelemetryPoller, SensorReading
provides:
  - Pillow peak-temperature tray icons (16/32px)
  - pystray orchestration loop wiring telemetry + alerts
  - Tkinter settings dialog with config persistence
  - save_config for hot-reload without restart
affects:
  - 04-integration-deployment

actuals:
  tokens: 85000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Injectable TrayIconController (PystrayTrayController / MockTrayController)"
    - "Background poll thread + blocking pystray.run()"
    - "Config hot-reload via save_config + _apply_config"

key-files:
  created:
    - src/ui/icon_renderer.py
    - src/ui/settings.py
    - src/ui/tray.py
    - tests/test_tray.py
    - .planning/phases/03-tray-ui-settings/03-RESEARCH.md
    - .planning/phases/03-tray-ui-settings/03-01-PLAN.md
  modified:
    - src/config/loader.py
    - src/config/schema.py
    - src/alerts/whatsapp.py

key-decisions:
  - "Red tint on tray icon when AlertEngine is alerting (Claude discretion per D-01)"
  - "MockTrayController for WSL tests — no real pystray display server (D-14)"
  - "API key field masked with show='*'; empty save preserves existing key (D-11)"
  - "CallMeBotClient.update_credentials for in-memory reload on settings save (D-09)"

patterns-established:
  - "MenuItemSpec dataclass for testable menu building independent of pystray"
  - "show_settings_dialog accepts injectable tk_module for headless tests"

requirements-completed: [TRAY-01, TRAY-02, TRAY-03, TRAY-04, CONF-01, CONF-02, CONF-03, CONF-04]

coverage:
  - id: D1
    description: "Peak integer rendered on Pillow tray icon"
    requirement: TRAY-01
    verification:
      - kind: unit
        ref: "tests/test_tray.py::test_peak_display_text_and_icon_render"
        status: pass
    human_judgment: false
  - id: D2
    description: "Tray poll updates icon and sensor menu each cycle"
    requirement: TRAY-02
    verification:
      - kind: unit
        ref: "tests/test_tray.py::test_tray_poll_updates_icon_and_menu"
        status: pass
    human_judgment: false
  - id: D3
    description: "Settings persist to config.json and reload in-memory"
    requirement: CONF-04
    verification:
      - kind: unit
        ref: "tests/test_tray.py::test_settings_save_persists_config"
        status: pass
    human_judgment: false
  - id: D4
    description: "Windows manual tray run via python -m src.ui.tray"
    requirement: TRAY-04
    verification: []
    human_judgment: true
    rationale: "Requires Windows display server and LHM DLL — not available on WSL CI"

duration: 15min
completed: 2026-08-16
status: complete
---

# Phase 3 Plan 1: Tray UI & Settings Summary

**Pillow peak-temperature tray icons with pystray orchestration, Tkinter settings persistence, and WSL-safe mocked tests.**

## Performance

- **Duration:** 15 min
- **Tasks:** 3/3
- **Files modified:** 11

## Accomplishments

- `icon_renderer.py` draws peak integer (or `--`) on 16×16 and 32×32 RGBA icons with red alerting tint
- `tray.py` orchestrates poll loop → icon/menu refresh → `AlertEngine.process_peak()` with clean Exit shutdown
- `settings.py` Tkinter modal for phone, masked API key, threshold with validation and `save_config`
- `save_config()` added to loader; `config_to_dict()` in schema; `CallMeBotClient.update_credentials()` for hot-reload
- 7 new tests in `test_tray.py` — all pass on WSL with mocked pystray/tkinter

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | (see git log) | Icon renderer + config save |
| 2 | (see git log) | Settings dialog |
| 3 | (see git log) | Tray orchestration + tests |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] CallMeBotClient.update_credentials**
- **Found during:** Task 3
- **Issue:** Settings hot-reload could not update WhatsApp credentials on existing client
- **Fix:** Added `update_credentials()` method to `CallMeBotClient`
- **Files modified:** `src/alerts/whatsapp.py`

None otherwise — plan executed as written.

## Self-Check: PASSED

- FOUND: src/ui/icon_renderer.py
- FOUND: src/ui/settings.py
- FOUND: src/ui/tray.py
- FOUND: tests/test_tray.py
- pytest: 31 passed (7 tray + 24 prior)
