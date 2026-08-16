# Phase 3: Tray UI & Settings - Research

**Researched:** 2026-08-16
**Domain:** pystray system tray, Pillow icon rendering, Tkinter settings dialog, telemetry+alert orchestration
**Confidence:** HIGH

## Summary

Phase 3 delivers the Windows system tray experience on top of Phase 1 telemetry and Phase 2 alerting. A single orchestration loop in `tray.py` polls sensors every 3 seconds, renders peak temperature digits on a Pillow canvas (`icon_renderer.py`), refreshes a pystray right-click menu with sensor detail labels, and calls `AlertEngine.process_peak(peak)` each cycle (D-12).

Settings use Tkinter modal dialog (`settings.py`) for phone, CallMeBot API key, and threshold (D-08). Save persists to `config/config.json` via new `save_config()` and reloads in-memory `AppConfig` without restart (D-09). WSL dev tests mock pystray and tkinter — no real tray on Linux (D-14).

**Primary recommendation:** Mirror Phase 1/2 injectable backend pattern for tray icon lifecycle; keep Pillow real in tests (cross-platform); mock pystray.Icon and tkinter modules for unit tests.

<user_constraints>
## User Constraints (from 03-CONTEXT.md)

### Tray Icon
- **D-01:** pystray + Pillow for tray lifecycle — **Reversibility:** costly
- **D-02:** Peak integer on 16×16 and 32×32 Pillow canvas — **Reversibility:** reversible
- **D-03:** Icon updates every poll cycle when peak changes — **Reversibility:** reversible
- **D-04:** When peak is None, show `--` or `??` — **Reversibility:** reversible

### Tray Menu
- **D-05:** Menu: sensor details, separator, Open Settings, Exit — **Reversibility:** reversible
- **D-06:** Sensor lines non-clickable, refreshed each poll — **Reversibility:** reversible
- **D-07:** Exit stops poller, beep, removes tray icon — **Reversibility:** reversible

### Settings Dialog
- **D-08:** Tkinter modal for phone, API key, threshold — **Reversibility:** reversible
- **D-09:** Load on open; Save writes config.json and reloads in-memory — **Reversibility:** reversible
- **D-10:** Validation threshold 1–150; error label on invalid save — **Reversibility:** reversible
- **D-11:** Mask API key (password entry or last 4 chars) — **Reversibility:** reversible

### Integration
- **D-12:** Single loop: poller → icon + menu + AlertEngine — **Reversibility:** reversible
- **D-13:** Runnable via `python -m src.ui.tray` on Windows — **Reversibility:** reversible
- **D-14:** WSL tests mock pystray/PIL/tkinter where needed — **Reversibility:** reversible
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRAY-01 | Peak temp integer on tray icon | D-02, icon_renderer.py Pillow canvas |
| TRAY-02 | Icon updates each poll cycle | D-03, tray poll thread updates icon.icon |
| TRAY-03 | Right-click menu shows all sensor details | D-05, D-06, pystray.MenuItem enabled=False |
| TRAY-04 | Open Settings and Exit actions | D-05, D-07, menu callbacks |
| CONF-01 | Configure WhatsApp phone | D-08, settings.py phone field |
| CONF-02 | Configure CallMeBot API key | D-08, D-11 masked entry |
| CONF-03 | Configure alarm threshold | D-08, D-10 validation |
| CONF-04 | Persist to config file, reload | D-09, save_config() in loader.py |
</phase_requirements>

## Standard Stack

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pystray | ≥0.19.5 [VERIFIED: requirements.txt:8] | System tray icon + menu | PROJECT.md decision (D-01) |
| Pillow | ≥10.0.0 [VERIFIED: requirements.txt:9] | Icon canvas rendering | D-02 digit rendering |
| tkinter | stdlib (Windows) | Settings dialog | D-08; no extra dep |
| threading | stdlib | Background poll loop | pystray.run() blocks main thread |

## Architecture Patterns

### Pattern 1: Background poll + blocking tray run
**What:** Daemon thread runs TelemetryPoller.run_once() loop; main thread runs pystray.Icon.run().
**When:** D-12 orchestration; icon/menu updates from poll thread (pystray thread-safe for icon property).

### Pattern 2: Injectable tray backend (tests)
**What:** `TrayIconController` protocol with PystrayController + MockTrayController.
**When:** D-14 WSL tests without pystray display server.

### Pattern 3: Config hot-reload on save
**What:** Settings save → save_config() → tray app replaces self._config and rebuilds AlertEngine clients if needed.
**When:** D-09 immediate effect without restart.

## Code Examples

### pystray dynamic menu (non-clickable labels)
```python
items = [pystray.MenuItem(f"{r.name}: {r.value_celsius:.0f}°C", None, enabled=False) for r in readings]
items += [pystray.Menu.SEPARATOR, pystray.MenuItem("Open Settings", on_settings), pystray.MenuItem("Exit", on_exit)]
icon.menu = pystray.Menu(*items)
```

### Pillow peak digit icon
```python
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGBA", (size, size), (40, 40, 40, 255))
draw = ImageDraw.Draw(img)
text = "--" if peak is None else str(int(round(peak)))
draw.text((2, 2), text, fill=(255, 255, 255, 255))
```

## Common Pitfalls

1. **Blocking poll in menu callback** — keep polling in daemon thread, not in pystray callbacks.
2. **tkinter from wrong thread** — open settings dialog from pystray menu callback (main tray thread); use Tk() per dialog.
3. **Forgetting stop_beep on exit** — D-07 requires AlertEngine sound stop and icon.stop().
4. **Saving placeholder API key** — if user leaves masked field unchanged, preserve existing key from config.

## Sources

- `src/telemetry/sensor_reader.py` — TelemetryPoller.run_once()
- `src/alerts/engine.py` — AlertEngine.process_peak()
- `src/config/loader.py` — load_config(); needs save_config()
- pystray docs — Icon.run(), MenuItem enabled=False for labels

**Research date:** 2026-08-16
