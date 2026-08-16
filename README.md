# CPU High Temperature Alert

Monitors CPU and GPU temperatures via LibreHardwareMonitor and alerts when sustained high temperatures are detected — audible PC beep plus WhatsApp notification via CallMeBot.

## Quick Start (Development)

### Requirements

- **Windows 10/11** with **64-bit Python 3.10+**
- **.NET Framework 4.7.2 or later** (required by LibreHardwareMonitor and pythonnet)
- Run `pip install -r requirements.txt` for runtime dependencies

### 1. Fetch LibreHardwareMonitor DLLs

```powershell
pwsh scripts/fetch-lhm.ps1
```

Downloads **LibreHardwareMonitor v0.9.6** from the official GitHub release into `vendor/LibreHardwareMonitor/`.

### 2. Configure CallMeBot WhatsApp

1. Add the CallMeBot WhatsApp contact to your phone: see [callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/)
2. Send the activation message to receive your API key
3. Copy the example config and edit credentials:

```powershell
mkdir config -Force
Copy-Item config/config.example.json config/config.json
notepad config/config.json
```

Set `whatsapp_phone` (E.164, e.g. `+1234567890`) and `callmebot_api_key`.

### 3. Run the Application

```powershell
python -m src.main
```

The app runs in the system tray with no console window when launched via `pythonw`:

```powershell
pythonw -m src.main
```

Tray icon shows peak temperature; right-click for sensor details, Settings, and Exit.

### Admin elevation

Admin elevation may improve GPU and driver sensor access on some systems. Autostart (below) registers with highest available privileges for better sensor coverage.

---

## Build Standalone `.exe` (Production)

The packaged executable does **not** require Python on the target machine. **.NET Framework 4.7.2+** is still required for LHM.

```powershell
pwsh scripts/build.ps1
```

Output: `dist/cpu-temp-alert/cpu-temp-alert.exe` (one-folder build with bundled LHM DLLs).

After building, copy config beside the executable:

```powershell
mkdir dist/cpu-temp-alert/config -Force
Copy-Item config/config.example.json dist/cpu-temp-alert/config/config.json
notepad dist/cpu-temp-alert/config/config.json
```

Run directly:

```powershell
.\dist\cpu-temp-alert\cpu-temp-alert.exe
```

---

## Autostart at Logon (Task Scheduler)

Install a scheduled task that starts the app silently at user logon with highest available privileges (no UAC prompt on each reboot after initial admin install):

**Packaged exe (recommended):**

```powershell
# Run PowerShell as Administrator
pwsh scripts/install-autostart.ps1
```

**Development mode** (uses `pythonw -m src.main` from repo):

```powershell
pwsh scripts/install-autostart.ps1 -DevMode
```

Verify:

```powershell
Get-ScheduledTask -TaskName CpuTempAlert | Format-List
```

Remove:

```powershell
Unregister-ScheduledTask -TaskName CpuTempAlert -Confirm:$false
```

---

## Manual End-to-End Test Checklist

Run on a **Windows machine** with LHM DLLs present. Check each item:

| # | Test | Expected |
|---|------|----------|
| 1 | `python -m src.main` | Tray icon appears; no console window with `pythonw` |
| 2 | Hover tray icon | Tooltip shows peak temperature |
| 3 | Right-click tray | Sensor names/values listed; Settings and Exit present |
| 4 | Open Settings → change threshold → Save | Values persist in `config/config.json`; icon still updates |
| 5 | Simulate high temp (stress test or lower threshold temporarily) | PC speaker beep starts within one poll cycle (~3s) |
| 6 | Drop temp below threshold | Beep stops immediately |
| 7 | First threshold breach with valid CallMeBot credentials | WhatsApp message received with peak/threshold/hostname |
| 8 | `pwsh scripts/build.ps1` then run `.exe` | Packaged app shows tray icon and reads sensors |
| 9 | `pwsh scripts/install-autostart.ps1` then reboot | App starts at logon without manual launch or UAC prompt |
| 10 | Exit from tray menu | Icon removed; beep stops; process exits |

---

## Telemetry CLI (Diagnostics)

For sensor debugging without the tray:

```powershell
python -m src.telemetry.sensor_reader
```

Prints CPU/GPU sensor names, values, and peak every 3 seconds.

Alert pipeline without tray:

```powershell
python -m src.alerts.harness
```

---

## Development on WSL2

WSL2 supports **unit tests only** (mocked LHM — no `clr` import). Real sensor, tray, winsound, and PyInstaller verification must run on Windows:

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/ -v
```

---

## Project Layout

```
src/main.py              Production entry point
src/ui/tray.py           Tray orchestration (TemperatureTrayApp)
src/telemetry/           LHM bridge and 3s poll loop
src/alerts/              Threshold engine, beep, WhatsApp
src/config/              config.json loader/schema
cpu-temp-alert.spec      PyInstaller spec
scripts/build.ps1        One-command Windows build
scripts/install-autostart.ps1  Task Scheduler setup
scripts/fetch-lhm.ps1    Download LHM DLL bundle
config/config.example.json   Example configuration (copy to config.json)
```
