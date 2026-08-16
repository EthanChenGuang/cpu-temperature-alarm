# Phase 1: Telemetry Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-16
**Phase:** 1-Telemetry Foundation
**Areas discussed:** Sensor selection, Invalid reading handling, Phase 1 dev output, LHM DLL provisioning

---

## Sensor Selection

| Option | Description | Selected |
|--------|-------------|----------|
| All Temperature sensors | Every LHM sensor with type Temperature on CPU/GPU | ✓ |
| Package + GPU only | Filter to Package/Tctl and primary GPU junction | |
| Package + GPU + hottest core | Max of Package, hottest core, GPU junction | |
| Max across all GPUs | Highest temp among all GPU sensors | ✓ |
| Max all CPU sockets | Include all CPU packages | ✓ |
| Hardware-prefixed names | e.g., "CPU / Package", "GPU / Hot Spot" | ✓ |
| Include auxiliaries | VRM, memory, hotspot count if type Temperature | ✓ |
| Skip inactive sensors | Ignore LHM inactive sensors | ✓ |

**User's choice:** All Temperature sensors; max across all GPUs and CPU sockets; hardware-prefixed names; include auxiliaries; skip inactive.
**Notes:** User requested extra follow-up on auxiliaries and inactive sensors before advancing.

---

## Invalid Reading Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Skip invalid values | Ignore ≤0°C or >150°C; warn once per sensor | ✓ |
| peak_temp = None | When all sensors invalid | ✓ |
| No smoothing | Raw per-poll peak | ✓ |
| Trust LHM per poll | No staleness timeout | ✓ |
| Peak from valid only | Partial failure doesn't block peak | ✓ |
| Warn once per sensor | Suppress repeat invalid warnings | ✓ |

**User's choice:** Skip invalid range; None peak when all invalid; no smoothing; no staleness check; peak from valid sensors only; warn once logging.
**Notes:** User explored logging verbosity and partial-failure behavior in follow-ups.

---

## Phase 1 Dev Output

| Option | Description | Selected |
|--------|-------------|----------|
| CLI + importable API | Console script and modules for Phase 2+ | ✓ |
| All sensors every poll | Timestamp, each sensor, peak every 3s | ✓ |
| stdout only | No log file in Phase 1 | ✓ |
| Mock-only on WSL | Real hardware tests on Windows | ✓ |
| Run until Ctrl+C | Continuous poll for manual test | ✓ |

**User's choice:** CLI + API; verbose console output; stdout; mocked WSL tests; Ctrl+C to exit.
**Notes:** Aligns with ROADMAP success criterion #1 (prints sensor names/values every 3s).

---

## LHM DLL Provisioning

| Option | Description | Selected |
|--------|-------------|----------|
| Bundled via fetch script | vendor/ populated by scripts/fetch-lhm.ps1 | ✓ |
| Document admin requirement | Don't hard-fail non-admin | ✓ |
| Clear error if missing DLL | Exit 1, typed API exception | ✓ |
| Document .NET prereq | README lists runtime requirement | ✓ |
| Pin stable LHM version | Specific release in fetch script | ✓ |
| No sensors: retry loop | Keep polling, peak=None | ✓ |

**User's choice:** Bundled fetch; document admin; graceful missing-DLL handling; document .NET; pin LHM version; poll on zero sensors.
**Notes:** User asked follow-up on version pinning and zero-sensor behavior.

---

## Claude's Discretion

None — user selected explicit options throughout; no "You decide" choices retained.

## Deferred Ideas

None captured during discussion.
