# Phase 2: Alert Engine - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart discuss — recommendations accepted)

<domain>
## Phase Boundary

Implement threshold-based alerting: local continuous beep while over threshold, WhatsApp notifications via CallMeBot with tier escalation (90°C, 95°C) and 3-minute cooldown per tier. Includes config loader for threshold and API credentials. Covers ALRT-01..05 only — no tray UI or packaging.

</domain>

<decisions>
## Implementation Decisions

### Alert Triggering & State Machine
- **D-01:** No alerting when `peak_temp is None` — treat as unknown, beep off, no WhatsApp — **Reversibility:** one-way — alert engine depends on Phase 1 None semantics
- **D-02:** State machine: `normal` → `alerting` → `cooldown`; transitions driven each poll cycle from telemetry peak — **Reversibility:** reversible
- **D-03:** Enter `alerting` when peak ≥ configured threshold (default 85°C); exit to `normal` immediately when peak drops below threshold (ALRT-02) — **Reversibility:** reversible
- **D-04:** Tier tracking is separate from base threshold: tiers at 90°C and 95°C (from config `critical_tiers_celsius`) trigger immediate WhatsApp re-alert even during cooldown (ALRT-04) — **Reversibility:** reversible
- **D-05:** Cooldown is per-tier: after WhatsApp sent for a tier, suppress duplicate messages for that tier for 180 seconds (ALRT-05); crossing a higher tier always sends immediately — **Reversibility:** reversible

### Local Sound (Beep)
- **D-06:** Use `winsound.Beep` in a daemon background thread while in `alerting` state (ALRT-01); stop thread immediately when peak drops below threshold (ALRT-02) — **Reversibility:** reversible
- **D-07:** Beep parameters from config: `beep_frequency_hz` (1000) and `beep_duration_ms` (500); loop beep with short gap between calls — **Reversibility:** reversible
- **D-08:** On WSL/non-Windows dev, inject a mock sound backend — no real winsound import in tests — **Reversibility:** reversible

### WhatsApp / CallMeBot
- **D-09:** HTTP GET to CallMeBot API with phone + apikey + URL-encoded message (ALRT-03) — **Reversibility:** reversible
- **D-10:** Message body uses config template `alert_message_template` with `{peak_temp}`, `{threshold}`, `{hostname}` placeholders — **Reversibility:** reversible
- **D-11:** Include tier in message when alerting on 90°C or 95°C tier (e.g., "CRITICAL tier 95°C") — **Reversibility:** reversible
- **D-12:** Log HTTP failures; do not crash poller — retry on next poll cycle if still over threshold and cooldown allows — **Reversibility:** reversible
- **D-13:** Skip WhatsApp send if phone or api key missing/placeholder — log warning once — **Reversibility:** reversible

### Configuration
- **D-14:** Load from `config/config.json` (user file, gitignored); fall back to defaults matching `config/config.example.json` — **Reversibility:** reversible
- **D-15:** Config fields: `threshold_celsius`, `critical_tiers_celsius`, `cooldown_seconds`, `whatsapp_phone`, `callmebot_api_key`, beep settings, message template — **Reversibility:** reversible
- **D-16:** `src/config/loader.py` + `schema.py` with validation (threshold 1–150, tiers sorted ascending) — **Reversibility:** reversible

### Integration with Telemetry
- **D-17:** Alert engine accepts peak temp from `read_sensors()` / poller callback each cycle — does not duplicate telemetry polling in Phase 2 standalone tests — **Reversibility:** reversible
- **D-18:** Phase 2 deliverable includes a minimal CLI or test harness wiring telemetry poll → alert engine for manual verification on Windows — **Reversibility:** reversible

### Claude's Discretion
Implementation details of thread lifecycle, exact CallMeBot URL format, and internal state dataclass shapes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Architecture
- `.planning/ROADMAP.md` — Phase 2 goal, deliverables, success criteria
- `.planning/REQUIREMENTS.md` — ALRT-01..05
- `.planning/PROJECT.md` — CallMeBot decision, tier escalation, cooldown constraints
- `.planning/phases/01-telemetry-foundation/01-CONTEXT.md` — peak_temp None semantics (D-08)

### Configuration
- `config/config.example.json` — Default threshold 85, tiers [90,95], cooldown 180s, beep settings
- `config/config.schema.json` — Field validation rules

### Implemented Telemetry (Phase 1)
- `src/telemetry/sensor_reader.py` — `read_sensors()`, `TelemetryPoller`, peak computation
- `src/telemetry/lhm_wrapper.py` — injectable bridge pattern for testing

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/telemetry/sensor_reader.py` — `TelemetryPoller` with callback hook for alert integration
- Injectable backend pattern from `LhmBridge` — reuse for `SoundBackend`, `WhatsAppClient` mocks
- `config/config.example.json` + `config.schema.json` — schema already defined

### Established Patterns
- Lazy platform imports (pythonnet in lhm_wrapper) — apply to winsound in sound.py
- WSL-safe tests with injected fakes — required for alerts tests
- stdout logging in Phase 1 — continue for alert state transitions in dev harness

### Integration Points
- Alert engine called each poll cycle after peak computed
- Phase 3 tray will show alert state; Phase 4 main.py wires telemetry + alerts

</code_context>

<specifics>
## Specific Ideas

- Broken cooling fans — beep must start within one poll cycle (3s) of threshold breach
- User obtains CallMeBot API key separately — graceful skip when not configured
- Tier escalation must bypass cooldown — critical for worsening thermal emergency

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Alert Engine*
*Context gathered: 2026-08-16*
