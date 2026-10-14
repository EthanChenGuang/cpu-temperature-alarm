# Elevated Windows integration test — writes log to $env:TEMP\cpu-admin-test-results.txt
$ErrorActionPreference = "Continue"
$LogPath = Join-Path $env:TEMP "cpu-admin-test-results.txt"
$Dst = "C:\dev\cpu-high-temperature-alert"
$Src = "\\wsl.localhost\Ubuntu\home\guang\Projects\Experiments\cpu-high-temperature-alert"
$Py = "C:\Users\Guang\AppData\Local\Programs\Python\Python313\python.exe"

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $LogPath -Value $line
}

"" | Set-Content $LogPath
Log "=== CPU High Temperature Alert — Admin Windows Test ==="

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Log "Running as Administrator: $isAdmin"
if (-not $isAdmin) {
    Log "FAIL: Not elevated — aborting"
    exit 1
}

# Sync project to local NTFS path (required for .NET DLL load)
Log "Syncing project to $Dst ..."
if (Test-Path $Dst) { Remove-Item -Recurse -Force $Dst }
New-Item -ItemType Directory -Force -Path $Dst | Out-Null
robocopy $Src $Dst /E /XD .venv .git __pycache__ .pytest_cache /NFL /NDL /NJH /NJS /NC /NS | Out-Null
Set-Location $Dst

# Fetch LHM
Log "Running fetch-lhm.ps1 ..."
& (Join-Path $Dst "scripts\fetch-lhm.ps1")

# Dependencies
Log "Installing Python dependencies ..."
& $Py -m pip install -q -r requirements.txt -r requirements-dev.txt
& $Py -m pip install -q "pyinstaller>=6.0.0"

if (-not (Test-Path "config\config.json")) {
    Copy-Item config\config.example.json config\config.json
}

# Pytest
Log "--- pytest ---"
$pytestOut = & $Py -m pytest tests/ -q 2>&1 | Out-String
Log $pytestOut.Trim()

# Live LHM read
Log "--- Live LHM (admin) ---"
$lhmScript = @"
import sys, time
sys.path.insert(0, r'$Dst')
from src.telemetry.lhm_wrapper import LhmBridge
from src.telemetry.sensor_reader import read_sensors
bridge = LhmBridge()
t0 = time.time()
bridge.open()
print(f'Open OK in {time.time()-t0:.1f}s')
snap = read_sensors(bridge)
print(f'Sensor count: {len(snap.readings)}')
for r in snap.readings:
    print(f'  {r.name}: {r.value_celsius:.1f}C')
print(f'Peak: {snap.peak_temp}')
cpu = [r for r in snap.readings if r.name.startswith('CPU')]
print(f'CPU sensors: {len(cpu)}')
"@
$lhmFile = Join-Path $env:TEMP "lhm-admin-read.py"
$lhmScript | Out-File -Encoding utf8 $lhmFile
$lhmOut = & $Py $lhmFile 2>&1 | Out-String
Log $lhmOut.Trim()

# Poll loop (2 cycles)
Log "--- sensor_reader 2 cycles ---"
$job = Start-Job -ScriptBlock {
    param($Py, $Dst)
    Set-Location $Dst
    $env:PYTHONUNBUFFERED = "1"
    & $Py -u -m src.telemetry.sensor_reader 2>&1
} -ArgumentList $Py, $Dst
Wait-Job $job -Timeout 8 | Out-Null
Stop-Job $job -ErrorAction SilentlyContinue
$pollOut = Receive-Job $job | Out-String
Remove-Job $job -Force -ErrorAction SilentlyContinue
Log ($pollOut -replace '(?m)^\s+$', '').Trim()

# Winsound beep test (threshold forced low in memory)
Log "--- winsound beep test (threshold=50) ---"
$beepScript = @"
import sys, time
sys.path.insert(0, r'$Dst')
from dataclasses import replace
from src.config.loader import load_config
from src.alerts.engine import AlertEngine
from src.alerts.sound import WinsoundBackend
from src.alerts.whatsapp import MockWhatsAppClient
from src.telemetry.lhm_wrapper import LhmBridge
from src.telemetry.sensor_reader import read_sensors
cfg = replace(load_config(), threshold_celsius=50)
bridge = LhmBridge()
bridge.open()
peak = read_sensors(bridge).peak_temp
sound = WinsoundBackend()
wa = MockWhatsAppClient()
engine = AlertEngine(cfg, sound, wa)
engine.process_peak(peak)
alive = sound._thread is not None and sound._thread.is_alive()
print(f'peak={peak} engine_state={engine.state.value} beep_thread_alive={alive}')
time.sleep(2)
engine.process_peak(30.0)
alive2 = sound._thread is not None and sound._thread.is_alive()
print(f'after below threshold engine_state={engine.state.value} beep_thread_alive={alive2}')
"@
$beepFile = Join-Path $env:TEMP "beep-admin-test.py"
$beepScript | Out-File -Encoding utf8 $beepFile
$beepOut = & $Py $beepFile 2>&1 | Out-String
Log $beepOut.Trim()

# Build exe
Log "--- PyInstaller build ---"
try {
    & (Join-Path $Dst "scripts\build.ps1") 2>&1 | ForEach-Object { Log $_ }
    $exe = Join-Path $Dst "dist\cpu-temp-alert\cpu-temp-alert.exe"
    if (Test-Path $exe) {
        Log "PASS: Build output exists — $exe"
        $exeSize = (Get-Item $exe).Length
        Log "Exe size: $([math]::Round($exeSize/1MB, 2)) MB"
        New-Item -ItemType Directory -Force -Path (Join-Path $Dst "dist\cpu-temp-alert\config") | Out-Null
        Copy-Item (Join-Path $Dst "config\config.json") (Join-Path $Dst "dist\cpu-temp-alert\config\config.json") -Force
        Log "Starting packaged exe for 8s ..."
        $proc = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 8
        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Log "PASS: Packaged exe ran 8s without crash (tray may be visible)"
        } else {
            Log "WARN: Packaged exe exited early with code $($proc.ExitCode)"
        }
    } else {
        Log "FAIL: Build exe not found"
    }
} catch {
    Log "FAIL: Build error — $($_.Exception.Message)"
}

# Task Scheduler (DevMode)
Log "--- Task Scheduler (DevMode) ---"
try {
    & (Join-Path $Dst "scripts\install-autostart.ps1") -DevMode 2>&1 | ForEach-Object { Log $_ }
    $task = Get-ScheduledTask -TaskName "CpuTempAlert" -ErrorAction SilentlyContinue
    if ($task) {
        Log "PASS: Scheduled task 'CpuTempAlert' registered"
        Log "  State: $($task.State)"
    } else {
        Log "FAIL: Task not found after install-autostart"
    }
} catch {
    Log "FAIL: install-autostart — $($_.Exception.Message)"
}

Log "=== Test complete. Log: $LogPath ==="
