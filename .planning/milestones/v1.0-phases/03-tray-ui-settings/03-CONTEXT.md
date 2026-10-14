# Phase 3: Tray UI & Settings - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart discuss — recommendations accepted)

<domain>
## Phase Boundary

Build system tray experience: dynamic temperature icon with peak integer, right-click menu with sensor details and Settings/Exit, Tkinter settings dialog with persistent config. Wire telemetry + alerts into tray update loop. Covers TRAY-01..04 and CONF-01..04 — no PyInstaller or Task Scheduler.

</domain>

<decisions>
## Implementation Decisions

### Tray Icon
- **D-01:** Use pystray + Pillow for tray icon lifecycle (per PROJECT.md) — **Reversibility:** costly
- **D-02:** Render peak temperature as integer digits on 16×16 and 32×32 Pillow canvas (`icon_renderer.py`) — **Reversibility:** reversible
- **D-03:** Icon updates every poll cycle (3s) when peak changes — **Reversibility:** reversible
- **D-04:** When `peak_temp is None`, show `--` or `??` on icon — **Reversibility:** reversible

### Tray Menu
- **D-05:** Right-click menu sections: sensor details (all hardware-prefixed names + values), separator, Open Settings, Exit — **Reversibility:** reversible
- **D-06:** Sensor detail lines are non-clickable labels refreshed each poll — **Reversibility:** reversible
- **D-07:** Exit stops poller, stops beep, removes tray icon, clean shutdown — **Reversibility:** reversible

### Settings Dialog
- **D-08:** Tkinter modal dialog for phone, CallMeBot API key, threshold °C (CONF-01..03) — **Reversibility:** reversible
- **D-09:** Load current values from config on open; Save writes `config/config.json` and reloads in-memory config without app restart (CONF-04) — **Reversibility:** reversible
- **D-10:** Basic validation: threshold 1–150, phone non-empty optional, show error label on invalid save — **Reversibility:** reversible
- **D-11:** Mask API key field (show last 4 chars or password entry) — **Reversibility:** reversible

### Integration
- **D-12:** Single orchestration loop in `tray.py`: TelemetryPoller callback → update icon + menu + AlertEngine.evaluate(peak) — **Reversibility:** reversible
- **D-13:** Phase 3 deliverable runnable via `python -m src.ui.tray` on Windows for manual test — **Reversibility:** reversible
- **D-14:** WSL tests mock pystray/PIL/tkinter where needed; no real tray on Linux — **Reversibility:** reversible

### Claude's Discretion
Icon color scheme (red tint when alerting), font choice for digits, exact menu ordering.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md` — Phase 3 deliverables and success criteria
- `.planning/REQUIREMENTS.md` — TRAY-01..04, CONF-01..04
- `.planning/PROJECT.md` — pystray, Pillow, Tkinter decisions
- `config/config.example.json`, `config/config.schema.json`
- `src/telemetry/sensor_reader.py`, `src/alerts/engine.py`, `src/config/loader.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 1 telemetry poller with callback
- Phase 2 AlertEngine + config loader
- Injectable backend pattern for tests

### Integration Points
- Phase 4 `main.py` will reuse tray orchestration from Phase 3

</code_context>

<specifics>
## Specific Ideas

- Peak integer must be readable at small tray sizes
- Settings changes take effect immediately without restart

</specifics>

<deferred>
## Deferred Ideas

- ENHN-01 configurable tier temps in settings (v2)
- ENHN-04 minimize-to-tray toast (v2)

</deferred>

---

*Phase: 3-Tray UI & Settings*
*Context gathered: 2026-08-16*
