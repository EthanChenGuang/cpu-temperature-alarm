# Phase 2: Alert Engine - Research

**Researched:** 2026-08-16
**Domain:** Python threshold alerting — winsound beep loop, CallMeBot WhatsApp HTTP, config validation
**Confidence:** HIGH

## Summary

Phase 2 adds a poll-driven alert engine on top of Phase 1 telemetry. Each poll cycle supplies `peak_temp: float | None` from `read_sensors()` / `TelemetryPoller.run_once()`; the engine drives local sound and optional WhatsApp notifications per locked decisions D-01 through D-18.

The stack is stdlib-heavy: `winsound` for Windows beep (lazy import + injectable mock backend per D-08), `requests` for CallMeBot GET (already pinned in `requirements.txt`), `threading` for the continuous beep loop (D-06, D-07), and `dataclasses` + `time.monotonic()` for per-tier cooldown tracking (D-05). Config loads from gitignored `config/config.json` with defaults from `config/config.example.json` (D-14, D-15).

CallMeBot sends WhatsApp via a single HTTP GET to `https://api.callmebot.com/whatsapp.php?phone={phone}&text={urlencoded_message}&apikey={key}` [CITED: https://www.callmebot.com/blog/free-api-whatsapp-messages/]. Failures are logged; the poller continues (D-12). Missing or placeholder credentials skip send with a one-time warning (D-13).

**Primary recommendation:** Implement injectable `SoundBackend` and `WhatsAppClient` protocols mirroring Phase 1 `LhmBackend`, with `AlertEngine.process_peak(peak_temp)` as the single poll-cycle entry point wired by a minimal harness CLI (D-18).

<user_constraints>
## User Constraints (from CONTEXT.md)

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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ALRT-01 | Continuous local Windows beep while peak exceeds threshold | D-06, D-07 — daemon thread + winsound.Beep loop in `alerting` state |
| ALRT-02 | Beep stops immediately when temp drops below threshold | D-03, D-06 — exit `alerting` → stop thread on same poll cycle |
| ALRT-03 | WhatsApp via CallMeBot on first threshold breach (85°C default) | D-09, D-10, D-13 — GET + template; base tier on first cross |
| ALRT-04 | Immediate re-alert at 90°C and 95°C tiers | D-04, D-11 — tier tracking bypasses cooldown |
| ALRT-05 | 3-minute cooldown suppresses duplicate WhatsApp for same tier | D-05 — per-tier monotonic timestamps |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Threshold / tier / cooldown logic | Application / Backend (`src/alerts/engine.py`) | — | Business rules; no UI in Phase 2 |
| Config load & validation | Application / Backend (`src/config/`) | — | Shared by alerts and future tray settings |
| Local sound output | OS integration (`src/alerts/sound.py`) | Application | winsound is Windows-only; abstracted for tests |
| WhatsApp HTTP | External integration (`src/alerts/whatsapp.py`) | Application | Outbound HTTP to CallMeBot |
| Telemetry peak input | Telemetry layer (`src/telemetry/sensor_reader.py`) | Application harness | Engine consumes peak; does not poll sensors in unit tests |
| Manual verification harness | Application CLI (`src/alerts/harness.py`) | — | Wires poller → engine for Windows manual test (D-18) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| winsound | stdlib (Windows) | Local beep | Native Windows PC speaker; project constraint |
| requests | ≥2.31.0,<3.0 [VERIFIED: requirements.txt:12] | CallMeBot HTTP GET | Already project dependency; simple GET API |
| threading | stdlib | Beep background loop | Standard pattern for non-blocking sound |
| dataclasses | stdlib | Config + engine state | Matches Phase 1 `SensorReading` pattern |
| urllib.parse.quote | stdlib | URL-encode WhatsApp message | Required by CallMeBot API [CITED: callmebot.com] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | ≥8.0.0 [VERIFIED: requirements-dev.txt:2] | Unit tests | WSL-safe alert tests with mocks |
| pytest-mock | ≥3.12.0 [VERIFIED: requirements-dev.txt:3] | HTTP mock | Optional; `unittest.mock` sufficient for requests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | urllib.request | requests already pinned; clearer timeout/error API |
| winsound.Beep loop | playsound / pygame | Extra dependency; winsound is Windows-native per PROJECT.md |
| CallMeBot | Twilio / Meta WhatsApp API | Out of scope per PROJECT.md |

**Installation:** No new runtime packages — `requests` already in `requirements.txt`. Dev: `pip install -r requirements-dev.txt`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| requests | PyPI | established | unknown (seam) | https://github.com/psf/requests | SUS | Pre-approved — already in requirements.txt; psf/requests is authoritative |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** requests (unknown-downloads from seam only; pre-pinned in project)

## Architecture Patterns

### System Architecture Diagram

```
TelemetryPoller.run_once() ──► peak_temp (float|None)
         │
         ▼
   AlertEngine.process_peak(peak_temp)
         │
    ┌────┴────┐
    ▼         ▼
SoundBackend  WhatsAppClient
 (beep thread)  (HTTP GET)
    │              │
    ▼              ▼
 winsound      api.callmebot.com
 (Windows)     /whatsapp.php
```

### Recommended Project Structure

```
src/
├── alerts/
│   ├── __init__.py
│   ├── engine.py      # State machine, tier/cooldown (D-02..D-05)
│   ├── sound.py       # SoundBackend protocol + WinsoundBackend + MockSoundBackend
│   ├── whatsapp.py    # WhatsAppClient protocol + CallMeBotClient
│   └── harness.py     # CLI: poller → engine loop (D-18)
├── config/
│   ├── __init__.py
│   ├── schema.py      # AppConfig dataclass + validate (D-16)
│   └── loader.py      # load_config() from config/config.json (D-14)
tests/
└── test_alerts.py     # Mock backends; no winsound/clr import
```

### Pattern 1: Injectable backend (mirror Phase 1 LhmBackend)
**What:** Protocol at module boundary; production impl lazy-imports platform deps; tests inject fakes.
**When to use:** winsound (D-08), HTTP client (test isolation).
**Example:** Follow `LhmBackend` / `LhmBridge` in `src/telemetry/lhm_wrapper.py:18-20`.

### Pattern 2: Poll-cycle state machine
**What:** `process_peak(peak)` called once per poll; idempotent transitions; no internal sleep loop except sound thread.
**When to use:** Every telemetry cycle (3s default).
**States:** `normal` (peak < threshold or None), `alerting` (peak ≥ threshold), `cooldown` (WhatsApp sent; beep may still run while over threshold).

### Pattern 3: Per-tier cooldown map
**What:** `dict[int, float]` mapping tier °C → last_sent_monotonic; check `time.monotonic() - last >= cooldown_seconds`.
**When to use:** Base threshold counts as tier `threshold_celsius`; critical tiers from `critical_tiers_celsius`.
**Tier bypass:** Higher tier not in map or expired → send immediately (D-04, D-05).

### Anti-Patterns to Avoid
- **Import winsound at module level:** Breaks WSL test collection (D-08).
- **Blocking HTTP in sound thread:** Keep network I/O on poll thread; only beep in background thread.
- **Global cooldown for all tiers:** Violates D-05 per-tier semantics.
- **Polling sensors inside AlertEngine:** Violates D-17; engine is pure consumer of peak.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL encoding message | Manual string replace | `urllib.parse.quote(message, safe='')` | CallMeBot requires proper encoding [CITED: callmebot.com] |
| HTTP GET client | Raw socket | `requests.get(url, timeout=10)` | Timeouts, status codes (D-12) |
| Config JSON parse | Custom parser | `json.load` + dataclass validation | schema.py validates ranges (D-16) |
| Thread stop signal | Process kill | `threading.Event` + join with timeout | Clean beep stop (D-02, D-06) |

**Key insight:** Phase 1 established injectable backends — reuse for sound and WhatsApp rather than patching platform checks into engine logic.

## Common Pitfalls

### Pitfall 1: Beep thread not stopping on threshold drop
**What goes wrong:** Beep continues after peak drops below threshold.
**Why it happens:** Stop signal not checked between Beep calls or thread not joined.
**How to avoid:** Check `threading.Event` before each Beep; call `stop_beep()` synchronously in `process_peak` when exiting `alerting` (D-02).
**Warning signs:** Tests show `mock_sound.beep_count` increasing after peak lowered.

### Pitfall 2: Tier escalation blocked by base-tier cooldown
**What goes wrong:** 95°C alert suppressed because 85°C tier still in cooldown.
**Why it happens:** Single global last_sent timestamp.
**How to avoid:** Separate cooldown keys per tier value; higher tier always evaluates send independently (D-04, D-05).

### Pitfall 3: Alerting on peak_temp None
**What goes wrong:** Spurious WhatsApp when sensors unavailable.
**Why it happens:** Treating None as 0 or ignoring None branch.
**How to avoid:** Early return in `process_peak`: stop beep, skip WhatsApp, reset to normal (D-01).

### Pitfall 4: Placeholder credentials spam logs
**What goes wrong:** Log warning every poll cycle.
**Why it happens:** No "warn once" guard for D-13.
**How to avoid:** Module-level or engine flag `_whatsapp_skip_warned`.

## Code Examples

### CallMeBot URL construction
```python
# Source: https://www.callmebot.com/blog/free-api-whatsapp-messages/
from urllib.parse import quote

base = "https://api.callmebot.com/whatsapp.php"
url = f"{base}?phone={phone}&text={quote(message, safe='')}&apikey={api_key}"
# requests.get(url, timeout=10)
```

### Default config values [VERIFIED: config/config.example.json:5-17]
```json
"threshold_celsius": 85,
"critical_tiers_celsius": [90, 95],
"cooldown_seconds": 180,
"beep_frequency_hz": 1000,
"beep_duration_ms": 500,
"alert_message_template": "CPU/GPU ALERT: Peak temperature {peak_temp}°C exceeds threshold {threshold}°C on {hostname}."
```

### Config validation bounds
- D-16: threshold 1–150, tiers sorted ascending (user decision)
- JSON schema file uses 40–110 [VERIFIED: config/config.schema.json:18-30] — loader implements D-16 bounds in Python validation

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WMI-only temps | LHM + pythonnet (Phase 1) | 2026-08-16 | Alerts consume `peak_temp` from Phase 1 API |
| N/A | CallMeBot free tier | Project decision | No OAuth; API key from bot activation |

**Deprecated/outdated:** None for this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CallMeBot accepts `+` in phone query param unencoded | Code Examples | URL encode phone if 4xx; test on Windows |
| A2 | Base threshold breach uses tier key `threshold_celsius` for cooldown | Pattern 3 | Clarify in engine: first WhatsApp at 85°C is tier 85 |

**If this table is empty:** N/A — assumptions listed above.

## Open Questions (RESOLVED)

1. **Base tier vs critical tier cooldown keys** — RESOLVED: Treat `threshold_celsius` as the base tier key; `critical_tiers_celsius` entries are additional tier keys (D-04, D-05).
2. **Modify TelemetryPoller for callback?** — RESOLVED: No — harness calls `run_once()` then `engine.process_peak(peak)` per D-17/D-18 without changing Phase 1 poller API.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All modules | ✓ (dev WSL) | 3.12.3 | — |
| winsound | ALRT-01/02 (Windows) | ✗ on WSL | stdlib | MockSoundBackend (D-08) |
| requests | ALRT-03 | ✓ (pinned) | ≥2.31 | — |
| pytest | tests | ✗ (not installed globally) | — | pip install -r requirements-dev.txt |
| CallMeBot API | ALRT-03 | external | — | Skip when unconfigured (D-13) |

**Missing dependencies with no fallback:**
- winsound on Windows target — required for production beep; available on Windows 10/11 only.

**Missing dependencies with fallback:**
- pytest on dev machine — install via requirements-dev.txt
- CallMeBot credentials — graceful skip (D-13)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — CallMeBot uses API key in URL |
| V5 Input Validation | yes | schema.py validates config ranges (D-16) |
| V6 Cryptography | no | HTTPS to CallMeBot; no local crypto |

### Known Threat Patterns for Python desktop + HTTP

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key in config.json | Information Disclosure | gitignore config.json [VERIFIED: .gitignore:11]; placeholder skip (D-13) |
| SSRF via config phone | Spoofing | Validate E.164 pattern; fixed CallMeBot host only |
| Log injection from template | Tampering | Format template with numeric peak only; no user-controlled template in Phase 2 |

## Sources

### Primary (HIGH confidence)
- `config/config.example.json` — default thresholds and template
- `config/config.schema.json` — field definitions
- `src/telemetry/sensor_reader.py` — peak_temp API, TelemetryPoller.run_once()
- `src/telemetry/lhm_wrapper.py` — injectable backend pattern

### Secondary (MEDIUM confidence)
- https://www.callmebot.com/blog/free-api-whatsapp-messages/ — URL format and activation steps

### Tertiary (LOW confidence)
- None material to phase implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib + existing project deps
- Architecture: HIGH — mirrors Phase 1 patterns
- Pitfalls: HIGH — locked decisions fully specify behavior

**Research date:** 2026-08-16
**Valid until:** 2026-09-16
