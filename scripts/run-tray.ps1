# Launch CPU Temp Alert in the foreground (normal user — tray icon visible).
# Double-click or: pwsh scripts/run-tray.ps1
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

$Candidates = @(
    (Join-Path (Join-Path $env:LOCALAPPDATA "Programs\cpu-temp-alert") "cpu-temp-alert.exe"),
    (Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert.exe"),
    (Join-Path (Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert") "cpu-temp-alert.exe")
)
foreach ($Exe in $Candidates) {
    if (Test-Path $Exe) {
        Start-Process -FilePath $Exe -WorkingDirectory (Split-Path -Parent $Exe)
        Write-Host "Started packaged app: $Exe"
        exit 0
    }
}

$VenvPython = Join-Path (Join-Path (Join-Path $RepoRoot ".venv") "Scripts") "python.exe"
if (Test-Path $VenvPython) {
    Start-Process -FilePath $VenvPython -ArgumentList "-m", "src.main" -WorkingDirectory $RepoRoot
    Write-Host "Started dev app via venv python"
    exit 0
}

Start-Process -FilePath "python" -ArgumentList "-m", "src.main" -WorkingDirectory $RepoRoot
Write-Host "Started dev app via system python"
