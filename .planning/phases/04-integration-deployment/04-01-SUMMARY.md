---
phase: 04-integration-deployment
plan: 01
subsystem: infra
tags: [pyinstaller, deployment, task-scheduler, main-entry, windows]

requires:
  - phase: 03-tray-ui-settings
    provides: TemperatureTrayApp orchestration, tray UI, config persistence
provides:
  - Production entry point src/main.py
  - PyInstaller one-folder spec with LHM DLL bundling
  - build.ps1 and install-autostart.ps1 deployment scripts
  - Full README runbook with E2E manual checklist
affects: []

actuals:
  tokens: 72000
  tasks: 3
  commits: 4

tech-stack:
  added: [pyinstaller]
  patterns:
    - "src/paths.py frozen vs dev app_root resolution"
    - "Thin main.py delegating to TemperatureTrayApp"
    - "One-folder COLLECT PyInstaller build with console=False"

key-files:
  created:
    - src/main.py
    - src/paths.py
    - cpu-temp-alert.spec
    - scripts/build.ps1
    - scripts/install-autostart.ps1
    - tests/test_main.py
    - .planning/phases/04-integration-deployment/04-RESEARCH.md
    - .planning/phases/04-integration-deployment/04-01-PLAN.md
    - .planning/phases/04-integration-deployment/04-VERIFICATION.md
  modified:
    - src/telemetry/lhm_wrapper.py
    - src/config/loader.py
    - src/ui/tray.py
    - README.md
    - requirements-dev.txt

key-decisions:
  - "One-folder COLLECT build over one-file for reliable pythonnet/LHM DLL loading"
  - "src/paths.py centralizes app_root for frozen exe and dev source tree"
  - "src/ui/tray.main() delegates to src.main for backward compatibility"
  - "install-autostart.ps1 supports -DevMode (pythonw) and packaged -ExePath"

patterns-established:
  - "Config and vendor paths resolve beside executable when sys.frozen"

requirements-completed: [DEPL-01, DEPL-02, DEPL-03]

coverage:
  - id: D1
    description: "python -m src.main wires full tray+telemetry+alert pipeline"
    requirement: DEPL-03
    verification:
      - kind: unit
        ref: "tests/test_main.py::test_main_wires_tray_app"
        status: pass
    human_judgment: false
  - id: D2
    description: "Frozen path resolution for vendor DLLs and config.json"
    requirement: DEPL-01
    verification:
      - kind: unit
        ref: "tests/test_main.py::test_app_root_dev_mode"
        status: pass
    human_judgment: false
  - id: D3
    description: "PyInstaller spec bundles LHM DLLs one-folder console=False"
    requirement: DEPL-01
    verification:
      - kind: other
        ref: "ast.parse(cpu-temp-alert.spec); datas vendor/LibreHardwareMonitor"
        status: pass
    human_judgment: false
  - id: D4
    description: "build.ps1 one-command Windows build wrapper"
    requirement: DEPL-01
    verification: []
    human_judgment: true
    rationale: "PyInstaller Windows exe build not runnable on WSL CI"
  - id: D5
    description: "install-autostart.ps1 Task Scheduler logon task Highest privileges"
    requirement: DEPL-02
    verification: []
    human_judgment: true
    rationale: "Register-ScheduledTask requires Windows admin PowerShell session"
  - id: D6
    description: "README runbook with CallMeBot, build, autorun, E2E checklist"
    requirement: DEPL-03
    verification:
      - kind: manual_procedural
        ref: "README.md Manual End-to-End Test Checklist (10 items)"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-08-16
status: complete
---

# Phase 4 Plan 1: Integration & Deployment Summary

**Production entry point with PyInstaller one-folder packaging, Task Scheduler autorun script, and full README deployment runbook.**

## Performance

- **Duration:** 20 min
- **Tasks:** 3/3
- **Files modified:** 14

## Accomplishments

- `src/main.py` canonical entry: config → LhmBridge → TemperatureTrayApp with winsound + CallMeBot
- `src/paths.py` resolves vendor/config beside frozen exe or repo root in dev
- `cpu-temp-alert.spec` one-folder COLLECT build, `console=False`, LHM DLL datas
- `scripts/build.ps1` runs fetch-lhm + PyInstaller; `scripts/install-autostart.ps1` registers CpuTempAlert logon task
- README expanded with Quick Start, CallMeBot setup, build, autorun, and 10-item E2E checklist
- 33/33 pytest PASS (2 new main entry tests)

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | c2fb007 | Production entry point with frozen path resolution |
| 2 | 093253e | PyInstaller spec and build script |
| 3 | 638d392 | Autostart script and README runbook |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: src/main.py
- FOUND: src/paths.py
- FOUND: cpu-temp-alert.spec
- FOUND: scripts/build.ps1
- FOUND: scripts/install-autostart.ps1
- FOUND: tests/test_main.py
- FOUND: .planning/phases/04-integration-deployment/04-01-SUMMARY.md
- FOUND: c2fb007, 093253e, 638d392
- pytest: 33 passed
