# Phase 4: Integration & Deployment - Research

**Researched:** 2026-08-16
**Domain:** Production entry point, PyInstaller packaging, Task Scheduler autorun, deployment runbook
**Confidence:** HIGH

## Summary

Phase 4 wires the completed Phase 1–3 modules into a production entry point (`src/main.py`), packages a Windows `.exe` via PyInstaller with bundled LHM DLLs, provides PowerShell scripts for build and Task Scheduler autorun, and documents the full install/configure/build/test runbook in README.md.

Phase 3 already implements `TemperatureTrayApp` orchestration in `src/ui/tray.py` with a working `main()`. Phase 4 promotes `src/main.py` as the canonical published entry point (D-01, D-03) while keeping `python -m src.ui.tray` as a backward-compatible alias.

**Primary recommendation:** One-folder PyInstaller build (not one-file) — LHM DLLs and pythonnet load more reliably when extracted beside the executable. Use `console=False` for silent tray-only operation (DEPL-03). Resolve `vendor/` and `config/` paths relative to executable directory when `sys.frozen`.

<user_constraints>
## User Constraints (from 04-CONTEXT.md)

### Main Entry Point
- **D-01:** `src/main.py` orchestrates load config → TelemetryPoller → AlertEngine → pystray tray — **Reversibility:** one-way
- **D-02:** No console window when packaged (DEPL-03) — **Reversibility:** reversible
- **D-03:** `python -m src.main` primary dev/prod invocation — **Reversibility:** reversible

### PyInstaller Packaging
- **D-04:** `cpu-temp-alert.spec` single-folder `.exe` (DEPL-01) — **Reversibility:** costly
- **D-05:** Bundle `vendor/LibreHardwareMonitor/*.dll` as datas — **Reversibility:** costly
- **D-06:** `scripts/build.ps1` wraps pyinstaller — **Reversibility:** reversible
- **D-07:** Document .NET required for LHM; Python not required when using `.exe` — **Reversibility:** reversible

### Task Scheduler Autostart
- **D-08:** `scripts/install-autostart.ps1` logon task, highest privileges, hidden window (DEPL-02) — **Reversibility:** reversible
- **D-09:** Task runs packaged `.exe` or `pythonw -m src.main` for dev — **Reversibility:** reversible

### Documentation & Testing
- **D-10:** README: install, CallMeBot, fetch LHM, build, manual test checklist — **Reversibility:** reversible
- **D-11:** E2E manual test checklist in README — **Reversibility:** reversible
- **D-12:** Update existing README, do not duplicate — **Reversibility:** reversible
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPL-01 | Standalone Windows `.exe` via PyInstaller | D-04, D-05, D-06, one-folder spec with DLL datas |
| DEPL-02 | Task Scheduler silent autorun at boot | D-08, D-09, install-autostart.ps1 |
| DEPL-03 | Background tray process, no console | D-02, console=False in spec; pythonw for dev autorun |
</phase_requirements>

## Standard Stack

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| PyInstaller | ≥6.0 | Windows `.exe` packaging | PROJECT.md decision; DEPL-01 |
| PowerShell | 5.1+ / pwsh | build.ps1, install-autostart.ps1 | Windows-native scripting |
| Task Scheduler | schtasks / Register-ScheduledTask | Autorun at logon | DEPL-02 silent boot |

## Architecture Patterns

### Pattern 1: Frozen path resolution
**What:** `app_root()` returns `Path(sys.executable).parent` when frozen, else repo root.
**When:** LHM vendor dir and config.json must resolve beside packaged exe, not source tree.

### Pattern 2: Thin main entry
**What:** `src/main.py` calls existing `TemperatureTrayApp` from `tray.py` — no duplicate orchestration logic.
**When:** D-01 published entry point without refactoring Phase 3 tray loop.

### Pattern 3: One-folder COLLECT build
**What:** PyInstaller `COLLECT` mode outputs `dist/cpu-temp-alert/` with exe + DLLs + dependencies.
**When:** pythonnet clr.AddReference needs filesystem paths to LHM DLLs (D-05).

## PyInstaller Spec Essentials

```python
# cpu-temp-alert.spec — key settings
a = Analysis(
    ['src/main.py'],
    datas=[('vendor/LibreHardwareMonitor', 'vendor/LibreHardwareMonitor')],
    hiddenimports=['clr', 'pystray', 'PIL', 'requests'],
)
exe = EXE(..., console=False, name='cpu-temp-alert')
coll = COLLECT(exe, a.binaries, a.datas, name='cpu-temp-alert')
```

## Task Scheduler Pattern

```powershell
$action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory (Split-Path $ExePath)
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "CpuTempAlert" -Action $action -Trigger $trigger `
    -RunLevel Highest -Settings $settings
```

Use `-WindowStyle Hidden` via `-Execute` with packaged exe (console=False) or `pythonw.exe` for dev.

## Common Pitfalls

1. **DLL path in frozen app** — `default_vendor_dir()` must not use `__file__` parents when frozen.
2. **Config beside exe** — users edit `config/config.json` next to install folder, not inside _MEIPASS.
3. **Building on WSL** — PyInstaller Windows exe must be built on Windows; spec and scripts are valid artifacts for WSL CI.
4. **Missing LHM DLLs at build time** — build.ps1 must run fetch-lhm.ps1 first or fail clearly.

## Sources

- `src/ui/tray.py` — TemperatureTrayApp, existing orchestration
- `src/telemetry/lhm_wrapper.py` — default_vendor_dir(), LhmBridge
- `src/config/loader.py` — default_config_path()
- PyInstaller docs — COLLECT, datas, console=False
- Phase 1 `scripts/fetch-lhm.ps1` — vendor layout

**Research date:** 2026-08-16
