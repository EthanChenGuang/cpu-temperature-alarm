# CPU High Temperature Alert

Monitors CPU and GPU temperatures via LibreHardwareMonitor and alerts when sustained high temperatures are detected.

## Telemetry Setup

Before first use on Windows, download the pinned LibreHardwareMonitor binaries:

```powershell
pwsh scripts/fetch-lhm.ps1
```

This fetches **LibreHardwareMonitor v0.9.6** from the official GitHub release and copies all required DLLs into `vendor/LibreHardwareMonitor/`.

### Requirements

- **Windows 10/11** with **64-bit Python 3.10+**
- **.NET Framework 4.7.2 or later** (required by pythonnet and LHM)
- Run `pip install -r requirements.txt` for runtime dependencies

### Running the telemetry CLI

```bash
python -m src.telemetry.sensor_reader
```

Prints a timestamp, every CPU/GPU sensor name and value, and peak temperature every 3 seconds until Ctrl+C.

### Admin elevation

Admin elevation may improve GPU and driver sensor access on some systems, but is **not required** to start the application. If sensors report null values without admin, try running once elevated.

### Development on WSL2

WSL2 is supported for **unit tests only** (mocked LHM backend — no `clr` import). Real sensor verification must run on the Windows target machine:

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/test_telemetry.py -v
```
