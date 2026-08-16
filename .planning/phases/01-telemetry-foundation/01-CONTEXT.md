# Phase 1: Telemetry Foundation - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the hardware telemetry layer: pin dependencies, integrate LibreHardwareMonitor via pythonnet, and deliver a 3-second poll that exposes all CPU/GPU temperature sensors and a single peak value. Covers TELE-01, TELE-02, TELE-03 only — no alerting, tray UI, or packaging.

</domain>

<decisions>
## Implementation Decisions

### Sensor Selection
- **D-01:** Include every LibreHardwareMonitor sensor with type `Temperature` on CPU and GPU hardware nodes when computing peak — **Reversibility:** costly — changing the filter later affects peak semantics and alert thresholds downstream
- **D-02:** GPU peak contribution = maximum across all detected GPUs (integrated + discrete) — **Reversibility:** reversible
- **D-03:** CPU peak contribution = maximum across all CPU sockets/packages — **Reversibility:** reversible
- **D-04:** Expose sensor names with hardware prefix (e.g., `CPU / Package`, `GPU / Hot Spot`) for downstream tray menu clarity — **Reversibility:** reversible
- **D-05:** Auxiliary temperature sensors (VRM, memory, hotspot, etc.) count toward peak if LHM reports them as type `Temperature` — **Reversibility:** reversible
- **D-06:** Skip sensors LHM marks inactive; do not include them in peak calculation — **Reversibility:** reversible

### Invalid Reading Handling
- **D-07:** Skip individual readings ≤0°C or >150°C when computing peak; log a WARNING once per sensor on first invalid value, suppress repeats until valid again — **Reversibility:** reversible
- **D-08:** When all sensors are skipped or invalid, set `peak_temp = None` (unknown); downstream phases must not alert on unknown peak — **Reversibility:** one-way — alert engine will depend on None semantics as "no data"
- **D-09:** No smoothing or debounce in Phase 1 — each 3-second poll computes peak independently from current valid readings — **Reversibility:** reversible
- **D-10:** No separate staleness timeout — trust LHM fresh read each poll cycle — **Reversibility:** reversible
- **D-11:** Partial sensor failure: compute peak from remaining valid sensors only; do not expose a separate "degraded" health flag in Phase 1 — **Reversibility:** reversible

### Phase 1 Dev Output & Testing
- **D-12:** Deliver both a runnable CLI (`python -m src.telemetry.sensor_reader`) and importable API (`lhm_wrapper`, `sensor_reader` modules) for Phase 2+ integration — **Reversibility:** reversible
- **D-13:** CLI prints timestamp, every sensor name + value, and peak summary every poll cycle (3s) — matches manual Windows verification need — **Reversibility:** reversible
- **D-14:** Log to stdout only in Phase 1; no rotating log file yet — **Reversibility:** reversible
- **D-15:** WSL2 development uses mocked LHM unit tests only; real sensor verification runs on Windows target machine — **Reversibility:** reversible
- **D-16:** CLI poll loop runs continuously until Ctrl+C — **Reversibility:** reversible

### LHM DLL Provisioning
- **D-17:** Bundle `LibreHardwareMonitorLib.dll` under `vendor/LibreHardwareMonitor/`, populated by `scripts/fetch-lhm.ps1` from official LHM release — **Reversibility:** costly — PyInstaller bundling in Phase 4 depends on vendor layout
- **D-18:** Document that admin elevation may be required once for full GPU/driver sensor access; do not hard-fail if running non-admin — **Reversibility:** reversible
- **D-19:** Missing DLL: log actionable error (run `fetch-lhm.ps1`), CLI exits with code 1, API raises typed exception; no crash/stack trace dump — **Reversibility:** reversible
- **D-20:** Document required .NET runtime version for pythonnet; clear error message if DLL load fails due to missing runtime — **Reversibility:** reversible
- **D-21:** Pin a specific stable LibreHardwareMonitor release version in `fetch-lhm.ps1`; document pinned version in README — **Reversibility:** reversible
- **D-22:** DLL loads but zero temperature sensors found: log clear message, keep polling every 3s (hardware may appear later), `peak_temp = None` — **Reversibility:** reversible

### Claude's Discretion
None — user made explicit choices for all presented options.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Architecture
- `.planning/ROADMAP.md` — Phase 1 goal, deliverables, success criteria, directory structure
- `.planning/REQUIREMENTS.md` — TELE-01..03 requirement definitions and traceability
- `.planning/PROJECT.md` — Core value, LHM/pythonnet decision, 3s polling constraint, WSL2 dev note

### Configuration & Dependencies
- `config/config.example.json` — `poll_interval_seconds: 3` (telemetry poll cadence)
- `config/config.schema.json` — Config field definitions including poll interval
- `requirements.txt` — Pinned `pythonnet` dependency for LHM bridge

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `requirements.txt` — `pythonnet>=3.0.3` already specified for LHM integration
- `config/config.example.json` — `poll_interval_seconds: 3` aligns with TELE poll cadence (loader not built until Phase 2; Phase 1 may hardcode 3s or read example for CLI default)

### Established Patterns
- Greenfield project — no `src/` code yet; ROADMAP defines target layout (`src/telemetry/lhm_wrapper.py`, `sensor_reader.py`, `tests/test_telemetry.py`)
- Planning artifacts in `.planning/`; config examples in `config/`

### Integration Points
- Phase 2 alert engine will consume peak temperature + per-sensor readings from telemetry API
- Phase 3 tray menu will display hardware-prefixed sensor names from telemetry API
- Phase 4 PyInstaller will bundle `vendor/LibreHardwareMonitor/` DLL tree

</code_context>

<specifics>
## Specific Ideas

- Manual Windows verification should mirror ROADMAP success criterion: print sensor names and values every 3 seconds with correct peak aggregation
- Broken cooling fans scenario — peak must reflect the hottest real sensor anywhere on CPU/GPU, hence "all Temperature sensors" and max-across-all-GPUs choices

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Telemetry Foundation*
*Context gathered: 2026-08-16*
