# CPU High Temperature Alert

## What This Is

A lightweight Windows system-tray desktop application written in Python that monitors CPU and GPU temperatures in real time, displays the current peak temperature on the tray icon, and alerts the user locally (continuous beep) and remotely (WhatsApp via CallMeBot) when temperatures exceed configurable safe thresholds. Built for a machine with broken cooling fans where immediate thermal awareness is critical.

## Core Value

The user is reliably warned — audibly and via WhatsApp — before hardware damage occurs from sustained high CPU/GPU temperatures.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Read CPU & GPU temperatures every 3 seconds via LibreHardwareMonitor
- [ ] Display peak temperature integer on system tray icon
- [ ] Trigger continuous local beep while over threshold
- [ ] Send WhatsApp alert via CallMeBot on threshold breach with tier escalation and 3-minute cooldown
- [ ] Provide settings UI for phone, API key, and threshold
- [ ] Package as standalone Windows `.exe` with Task Scheduler autorun

### Out of Scope

- Linux/macOS support — Windows-only target platform
- Cloud dashboard or multi-machine monitoring — single local machine only
- Fan speed control or hardware remediation — monitoring and alerting only
- Native WhatsApp Business API — CallMeBot free tier is sufficient
- GPU/CPU per-core detailed graphs — tray icon shows peak only; details in menu

## Context

- **Hardware situation:** Cooling fans are broken; user needs proactive thermal alerts.
- **Platform:** Windows desktop, runs silently in system tray at boot.
- **Telemetry source:** LibreHardwareMonitorLib.dll via `pythonnet` (preferred over WMI for GPU coverage).
- **Alert channel:** CallMeBot HTTP GET API for WhatsApp messages.
- **Development environment:** WSL2 for planning; build and test on Windows target machine.

## Constraints

- **Platform:** Windows 10/11 only — uses `winsound`, `pystray`, Task Scheduler
- **Polling:** 3-second interval — balance responsiveness vs. resource use
- **Alert rate limit:** 3-minute WhatsApp cooldown except tier escalation (90°C, 95°C)
- **Packaging:** PyInstaller single-file or one-folder `.exe`
- **Autostart:** Task Scheduler with elevated admin privileges to bypass UAC on boot
- **Dependencies:** `pythonnet` requires .NET runtime on target machine

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LibreHardwareMonitor via pythonnet | Broad CPU/GPU sensor coverage vs. WMI gaps | — Pending |
| pystray + Pillow for tray icon | Lightweight, proven Windows tray support | — Pending |
| Tkinter for settings UI | No extra GUI dependency; ships with Python | — Pending |
| Step-escalation alert tiers at 85/90/95°C | Immediate re-alert on worsening temps; cooldown prevents spam | — Pending |
| config.json for persistence | Simple, editable, PyInstaller-friendly | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-16 after initialization*
