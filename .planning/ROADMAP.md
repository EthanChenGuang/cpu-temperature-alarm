# Roadmap: CPU High Temperature Alert

**Project:** CPU High Temperature Alert
**Phases:** 4
**Requirements:** 18 v1 requirements, 100% mapped

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                             │
│              (orchestrator / entry point)                  │
└──────────┬──────────────┬──────────────┬──────────────────┘
           │              │              │
    ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
    │  telemetry/ │ │  alerts/  │ │    ui/    │
    │ lhm_wrapper │ │  engine   │ │   tray    │
    │sensor_reader│ │ whatsapp  │ │icon_render│
    │             │ │   sound   │ │ settings  │
    └──────┬──────┘ └─────┬─────┘ └─────┬─────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                   ┌──────▼──────┐
                   │   config/   │
                   │ loader/schema│
                   └─────────────┘
```

## Directory Structure

```
cpu-high-temperature-alert/
├── .planning/                    # GSD planning artifacts
├── src/
│   ├── __init__.py
│   ├── main.py                   # Application entry point & orchestrator
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── lhm_wrapper.py        # pythonnet bridge to LibreHardwareMonitorLib.dll
│   │   └── sensor_reader.py      # 3s poll loop, max-temp computation
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── engine.py             # Threshold, tier escalation, cooldown logic
│   │   ├── whatsapp.py           # CallMeBot HTTP GET integration
│   │   └── sound.py              # Async winsound beep loop
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── tray.py               # pystray icon lifecycle & menu
│   │   ├── icon_renderer.py      # Pillow canvas → peak temp integer
│   │   └── settings.py           # Tkinter settings dialog
│   └── config/
│       ├── __init__.py
│       ├── loader.py             # Load/save config.json
│       └── schema.py             # Defaults & validation
├── vendor/
│   └── LibreHardwareMonitor/     # Bundled DLL + dependencies
│       └── LibreHardwareMonitorLib.dll
├── config/
│   └── config.example.json       # Example config (committed)
├── scripts/
│   ├── build.ps1                 # PyInstaller build wrapper
│   ├── install-autostart.ps1     # Task Scheduler setup (admin)
│   └── fetch-lhm.ps1             # Download/extract LHM DLL bundle
├── tests/
│   ├── __init__.py
│   ├── test_telemetry.py
│   ├── test_alerts.py
│   └── test_config.py
├── requirements.txt
├── cpu-temp-alert.spec           # PyInstaller spec (Phase 4)
├── .gitignore
└── README.md
```

---

## Phase Summary

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Telemetry Foundation | Reliable CPU/GPU temperature reads via LHM | TELE-01..03 | 3 |
| 2 | Alert Engine | Threshold alerts with sound + WhatsApp | ALRT-01..05 | 4 |
| 3 | Tray UI & Settings | Visual tray icon and configuration | TRAY-01..04, CONF-01..04 | 4 |
| 4 | Integration & Deployment | End-to-end app, exe, autorun | DEPL-01..03 | 3 |

---

### Phase 1: Telemetry Foundation
**Goal:** Establish the hardware telemetry layer — dependencies, LibreHardwareMonitor DLL integration, and a working 3-second temperature poll that returns peak CPU/GPU temperature.
**Mode:** mvp
**Requirements:** TELE-01, TELE-02, TELE-03

**Deliverables:**
- `requirements.txt` with pinned dependencies
- `vendor/LibreHardwareMonitor/` DLL bundle + fetch script
- `src/telemetry/lhm_wrapper.py` — pythonnet bridge, sensor discovery
- `src/telemetry/sensor_reader.py` — poll loop, max-temp aggregation
- `tests/test_telemetry.py` — unit tests with mocked sensors

**Success Criteria:**
1. Running sensor reader on Windows prints CPU and GPU sensor names and values every 3 seconds
2. Peak temperature correctly reflects the highest value among all active CPU/GPU sensors
3. Graceful error when DLL missing or no sensors detected (clear log message, no crash)

---

### Phase 2: Alert Engine
**Goal:** Implement threshold-based alerting with local sound, WhatsApp notifications via CallMeBot, tier escalation, and 3-minute cooldown.
**Mode:** mvp
**Requirements:** ALRT-01, ALRT-02, ALRT-03, ALRT-04, ALRT-05

**Deliverables:**
- `src/alerts/engine.py` — state machine: normal → alerting → cooldown
- `src/alerts/whatsapp.py` — CallMeBot HTTP GET with message formatting
- `src/alerts/sound.py` — background thread with continuous `winsound.Beep` loop
- `src/config/loader.py` + `schema.py` — load threshold and API credentials
- `tests/test_alerts.py` — tier escalation, cooldown, beep start/stop logic

**Success Criteria:**
1. Beep starts within one poll cycle of exceeding threshold and stops when temp drops below
2. WhatsApp message sent on first breach; suppressed for 3 minutes on same tier
3. Immediate re-alert when temperature crosses 90°C or 95°C tiers regardless of cooldown

---

### Phase 3: Tray UI & Settings
**Goal:** Build the system tray experience — dynamic temperature icon, sensor detail menu, and Tkinter settings dialog with persistent config.
**Mode:** mvp
**Requirements:** TRAY-01, TRAY-02, TRAY-03, TRAY-04, CONF-01, CONF-02, CONF-03, CONF-04

**Deliverables:**
- `src/ui/icon_renderer.py` — Pillow 16×16/32×32 icon with temperature digits
- `src/ui/tray.py` — pystray icon, menu (Details, Settings, Exit)
- `src/ui/settings.py` — Tkinter dialog for phone, API key, threshold
- `config/config.example.json` — documented schema
- Wire telemetry + alerts into tray update loop

**Success Criteria:**
1. Tray icon shows current peak temperature integer and updates every poll cycle
2. Right-click menu lists all sensor names with current values
3. Settings changes persist to config.json and take effect without restart

---

### Phase 4: Integration & Deployment
**Goal:** Wire all modules into a production entry point, document testing, package as Windows `.exe`, and provide Task Scheduler autorun setup.
**Mode:** mvp
**Requirements:** DEPL-01, DEPL-02, DEPL-03

**Deliverables:**
- `src/main.py` — orchestrator: config → telemetry → alerts → tray
- `cpu-temp-alert.spec` — PyInstaller spec with DLL bundling
- `scripts/build.ps1` — one-command build
- `scripts/install-autostart.ps1` — Task Scheduler XML + registration
- `README.md` — install, configure, build, and test runbook
- End-to-end manual test checklist

**Success Criteria:**
1. `python -m src.main` runs silently in tray with full alert pipeline on Windows
2. PyInstaller produces a working `.exe` that reads sensors and sends alerts
3. Task Scheduler script creates autorun entry that survives reboot without UAC prompt

---

## Phase Dependencies

```
Phase 1 (Telemetry)
    └──► Phase 2 (Alerts) — needs temperature readings
              └──► Phase 3 (UI) — needs alert engine + readings for tray
                        └──► Phase 4 (Deploy) — needs all modules integrated
```

---
*Roadmap created: 2026-08-16*
