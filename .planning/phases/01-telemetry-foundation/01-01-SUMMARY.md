---
phase: 01-telemetry-foundation
plan: 01
subsystem: api
tags: [pythonnet, librehardwaremonitor, telemetry, pytest, wsl]

requires: []
provides:
  - Injectable LhmBridge with lazy clr import and vendor DLL layout
  - 3-second TelemetryPoller CLI and read_sensors importable API
  - WSL-safe mocked unit test suite for peak semantics
  - fetch-lhm.ps1 pinned to LibreHardwareMonitor v0.9.6
affects: [02-alerts, 03-ui, 04-packaging]

actuals:
  tokens: 5011
  tasks: 3
  commits: 4

tech-stack:
  added: [pythonnet bridge pattern, pytest, pytest-mock]
  patterns: [injectable LhmBackend protocol, lazy clr in open(), pure compute_peak]

key-files:
  created:
    - scripts/fetch-lhm.ps1
    - src/telemetry/lhm_wrapper.py
    - src/telemetry/sensor_reader.py
    - src/telemetry/exceptions.py
    - tests/test_telemetry.py
    - requirements-dev.txt
    - README.md
  modified:
    - .gitignore

key-decisions:
  - "Lazy clr import confined to LhmBridge.open() for WSL testability (D-15)"
  - "Peak computed as max of valid (>0, <=150) readings with None when empty (D-07, D-08)"
  - "Vendor DLLs gitignored; fetch-lhm.ps1 is sole provisioning path (D-17, T-01-02)"

patterns-established:
  - "Pattern: Injectable LhmBackend protocol at wrapper boundary for mocks"
  - "Pattern: Recursive hardware Update before sensor read each poll cycle"

requirements-completed: [TELE-01, TELE-02, TELE-03]

coverage:
  - id: D1
    description: "fetch-lhm.ps1 downloads pinned LHM v0.9.6 DLLs to vendor/"
    requirement: TELE-01
    verification:
      - kind: unit
        ref: "scripts/fetch-lhm.ps1 grep 0.9.6"
        status: pass
    human_judgment: false
  - id: D2
    description: "Peak temperature is max of valid CPU+GPU readings or None"
    requirement: TELE-03
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_compute_peak_*"
        status: pass
    human_judgment: false
  - id: D3
    description: "Invalid readings skipped with deduplicated WARNING logs"
    requirement: TELE-03
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_compute_peak_warns_once_per_sensor"
        status: pass
    human_judgment: false
  - id: D4
    description: "Missing DLL exits CLI 1 with fetch-lhm.ps1 message, no traceback"
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_main_exits_one_on_missing_dll"
        status: pass
    human_judgment: false
  - id: D5
    description: "Zero sensors logs message and keeps polling with peak None"
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_run_forever_empty_sensors_logs_message"
        status: pass
    human_judgment: false
  - id: D6
    description: "Windows CLI prints timestamp, sensors, and peak every 3s until Ctrl+C"
    requirement: TELE-01
    verification: []
    human_judgment: true
    rationale: "Requires Windows host with LHM DLL and hardware sensors; WSL tests use mocks only (D-15)"

duration: 12min
completed: 2026-08-16
status: complete
---

# Phase 1 Plan 01: Telemetry Foundation Summary

**LibreHardwareMonitor v0.9.6 bridge with injectable pythonnet wrapper, 3-second poll CLI, peak aggregation API, and 15 WSL-safe mocked tests**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-16T19:55:00Z
- **Completed:** 2026-08-16T19:57:20Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Created `scripts/fetch-lhm.ps1` pinned to LibreHardwareMonitor v0.9.6 with idempotent vendor DLL extraction
- Implemented `LhmBridge` with lazy `clr` import, recursive hardware Update, and CPU/GPU temperature enumeration
- Built `TelemetryPoller` CLI and `read_sensors()` importable API with peak filtering per D-01 through D-11
- Added 15 pytest tests covering peak semantics, error paths, and output formatting without importing clr on WSL

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end telemetry poll tracer slice** - `24b725b` (feat)
2. **Task 2: Full sensor enumeration, peak semantics, and error paths** - `6461fd6` (test), `6026f3e` (feat)
3. **Task 3: Dev test harness and requirements-dev.txt** - `f48a743` (feat)

## Files Created/Modified

- `scripts/fetch-lhm.ps1` - Downloads and extracts LHM v0.9.6 DLLs to vendor/
- `src/telemetry/lhm_wrapper.py` - Injectable LHM bridge with SensorReading dataclass
- `src/telemetry/sensor_reader.py` - Poll loop, compute_peak, read_sensors API, CLI entry
- `src/telemetry/exceptions.py` - LhmDllNotFoundError and LhmRuntimeError
- `tests/test_telemetry.py` - 15 WSL-safe unit tests with FakeLhmBackend
- `requirements-dev.txt` - pytest and pytest-mock pins
- `README.md` - Telemetry setup, .NET runtime, admin note, WSL dev workflow
- `.gitignore` - Excludes vendored `*.dll` binaries

## Decisions Made

- Lazy `clr` import only inside `LhmBridge.open()` to keep WSL test collection clean (D-15)
- `compute_peak` maintains warned_sensors set on poller for deduplicated WARNING logs (D-07)
- Empty sensor list logs once per empty-state transition, continues polling (D-22)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required. Windows users must run `pwsh scripts/fetch-lhm.ps1` before first telemetry use.

## Next Phase Readiness

- Phase 2 alert engine can import `read_sensors()` and consume `peak_temp` / per-sensor readings
- Windows manual verification of live sensors remains pending (human judgment item D6)

## Self-Check: PASSED

- FOUND: scripts/fetch-lhm.ps1
- FOUND: src/telemetry/lhm_wrapper.py
- FOUND: src/telemetry/sensor_reader.py
- FOUND: tests/test_telemetry.py
- FOUND: requirements-dev.txt
- FOUND: README.md
- FOUND: 24b725b, 6461fd6, 6026f3e, f48a743

---
*Phase: 01-telemetry-foundation*
*Completed: 2026-08-16*
