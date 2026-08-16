# Build CPU High Temperature Alert Windows executable via PyInstaller
# Usage: pwsh scripts/build.ps1
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VendorDll = Join-Path $RepoRoot "vendor" "LibreHardwareMonitor" "LibreHardwareMonitorLib.dll"
$SpecPath = Join-Path $RepoRoot "cpu-temp-alert.spec"
$DistDir = Join-Path $RepoRoot "dist" "cpu-temp-alert"

Set-Location $RepoRoot

if (-not (Test-Path $VendorDll)) {
    Write-Host "LHM DLLs not found — running fetch-lhm.ps1"
    & (Join-Path $RepoRoot "scripts" "fetch-lhm.ps1")
}

$VenvPython = Join-Path $RepoRoot ".venv" "Scripts" "python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Write-Host "Installing PyInstaller (if needed)..."
& $Python -m pip install -q "pyinstaller>=6.0.0"

Write-Host "Building with PyInstaller..."
& $Python -m PyInstaller $SpecPath --noconfirm --clean

$ExePath = Join-Path $DistDir "cpu-temp-alert.exe"
if (-not (Test-Path $ExePath)) {
    throw "Build failed — expected $ExePath"
}

Write-Host ""
Write-Host "Build complete: $ExePath"
Write-Host "Copy config/config.example.json to dist/cpu-temp-alert/config/config.json and edit credentials."
Write-Host "Run: $ExePath"
