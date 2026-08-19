# CPU High Temperature Alert

## What This Is

A lightweight Windows system-tray desktop application written in Python that monitors CPU and GPU temperatures in real time, displays the current peak temperature on the tray icon, and alerts the user locally (continuous beep) and remotely (WhatsApp via CallMeBot) when temperatures exceed configurable safe thresholds. Built for a machine with broken cooling fans where immediate thermal awareness is critical.

## Core Value

The user is reliably warned — audibly and via WhatsApp — before hardware damage occurs from sustained high CPU/GPU temperatures.

## Requirements

### Validated

- ✓ Read CPU & GPU temperatures every 3 seconds via LibreHardwareMonitor — v1.0
- ✓ Display peak temperature integer on system tray icon — v1.0
- ✓ Trigger continuous local beep while over threshold — v1.0
- ✓ Send WhatsApp alert via CallMeBot on threshold breach with tier escalation and 3-minute cooldown — v1.0
- ✓ Provide settings UI for phone, API key, and threshold — v1.0
- ✓ Package as standalone Windows `.exe` with Task Scheduler autorun — v1.0 (artifacts; Windows build verification pending)

### Active

(None — v1.0 shipped; define new requirements in next milestone)

### Out of Scope

- Linux/macOS support — Windows-only target platform
- Cloud dashboard or multi-machine monitoring — single local machine only
- Fan speed control or hardware remediation — monitoring and alerting only
- Native WhatsApp Business API — CallMeBot free tier is sufficient
- GPU/CPU per-core detailed graphs — tray icon shows peak only; details in menu

## Context

- **Hardware situation:** Cooling fans are broken; user needs proactive thermal alerts.
- **Platform:** Windows desktop, runs silently in system tray at boot.
- **Telemetry source:** LibreHardwareMonitorLib.dll v0.9.6 via `pythonnet`.
- **Alert channel:** CallMeBot HTTP GET API for WhatsApp messages.
- **Development environment:** WSL2 for dev/tests (33 mocked pytest tests); Windows target for live hardware validation.
- **Shipped v1.0:** 2026-08-19 — `python -m src.main`, PyInstaller spec, Task Scheduler script, README runbook.

## Constraints

- **Platform:** Windows 10/11 only — uses `winsound`, `pystray`, Task Scheduler
- **Polling:** 3-second interval — balance responsiveness vs. resource use
- **Alert rate limit:** 3-minute WhatsApp cooldown except tier escalation (90°C, 95°C)
- **Packaging:** PyInstaller one-folder `.exe` (COLLECT mode for DLL reliability)
- **Autostart:** Task Scheduler with elevated admin privileges to bypass UAC on boot
- **Dependencies:** `pythonnet` requires .NET runtime on target machine

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LibreHardwareMonitor via pythonnet | Broad CPU/GPU sensor coverage vs. WMI gaps | ✓ Good — LHM v0.9.6 pinned, injectable bridge |
| pystray + Pillow for tray icon | Lightweight, proven Windows tray support | ✓ Good — peak digits + red alert tint |
| Tkinter for settings UI | No extra GUI dependency; ships with Python | ✓ Good — hot-reload config without restart |
| Step-escalation alert tiers at 85/90/95°C | Immediate re-alert on worsening temps; cooldown prevents spam | ✓ Good — per-tier cooldown map |
| config.json for persistence | Simple, editable, PyInstaller-friendly | ✓ Good — save_config + schema validation |
| Injectable mock backends for WSL tests | Cannot run LHM/winsound/pystray on Linux | ✓ Good — 33/33 tests pass on WSL |
| One-folder PyInstaller build | Reliable pythonnet + LHM DLL loading | ✓ Good — spec + build.ps1; exe build unverified on WSL |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-08-19 after v1.0 milestone*
