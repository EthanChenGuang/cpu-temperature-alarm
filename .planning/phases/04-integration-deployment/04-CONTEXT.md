# Phase 4: Integration & Deployment - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart discuss — recommendations accepted)

<domain>
## Phase Boundary

Wire telemetry, alerts, and tray into production entry point; PyInstaller Windows `.exe`; Task Scheduler autorun script; README runbook. Covers DEPL-01..03 — final integration milestone.

</domain>

<decisions>
## Implementation Decisions

### Main Entry Point
- **D-01:** `src/main.py` orchestrates: load config → start TelemetryPoller → AlertEngine → pystray tray loop — **Reversibility:** one-way — published entry point
- **D-02:** Run as background process with no console window when packaged (DEPL-03) — **Reversibility:** reversible
- **D-03:** `python -m src.main` is primary dev/prod invocation — **Reversibility:** reversible

### PyInstaller Packaging
- **D-04:** Single-folder or one-file `.exe` via PyInstaller spec `cpu-temp-alert.spec` (DEPL-01) — **Reversibility:** costly
- **D-05:** Bundle `vendor/LibreHardwareMonitor/*.dll` as datas in spec — **Reversibility:** costly
- **D-06:** `scripts/build.ps1` wraps pyinstaller one-command build — **Reversibility:** reversible
- **D-07:** Document .NET runtime + Python not required on target when using `.exe` (except .NET for pythonnet/LHM) — **Reversibility:** reversible

### Task Scheduler Autostart
- **D-08:** `scripts/install-autostart.ps1` creates Task Scheduler entry at logon, highest available privileges, hidden window (DEPL-02) — **Reversibility:** reversible
- **D-09:** Task runs packaged `.exe` path or `pythonw -m src.main` for dev — **Reversibility:** reversible

### Documentation & Testing
- **D-10:** README.md: install, configure CallMeBot, fetch LHM, build, manual test checklist — **Reversibility:** reversible
- **D-11:** End-to-end manual test checklist in README or `.planning/` — **Reversibility:** reversible
- **D-12:** Update existing README from Phase 1/2/3 rather than duplicate — **Reversibility:** reversible

### Claude's Discretion
PyInstaller one-file vs one-folder tradeoff, exact Task Scheduler XML structure.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md` — Phase 4 deliverables
- `.planning/REQUIREMENTS.md` — DEPL-01..03
- All prior phase CONTEXT/SUMMARY files
- `src/telemetry/`, `src/alerts/`, `src/ui/`, `src/config/`

</canonical_refs>

<code_context>
## Existing Code Insights

Phases 1–3 modules ready for wiring in main.py. fetch-lhm.ps1 and vendor/ layout from Phase 1.

</code_context>

<specifics>
## Specific Ideas

- Silent boot autorun without UAC prompt each reboot
- Single exe for non-technical user on broken-fan machine

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---

*Phase: 4-Integration & Deployment*
*Context gathered: 2026-08-16*
