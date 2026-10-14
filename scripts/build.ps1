# Build CPU High Temperature Alert Windows executable via PyInstaller
# Usage:
#   pwsh scripts/build.ps1           # single-file exe (default)
#   pwsh scripts/build.ps1 -OneFolder
param(
    [switch]$OneFolder
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VendorDll = Join-Path (Join-Path (Join-Path $RepoRoot "vendor") "LibreHardwareMonitor") "LibreHardwareMonitorLib.dll"
$SpecPath = Join-Path $RepoRoot "cpu-temp-alert.spec"

Set-Location $RepoRoot

if (-not (Test-Path $VendorDll)) {
    Write-Host "LHM DLLs not found — running fetch-lhm.ps1"
    & (Join-Path $RepoRoot "scripts" "fetch-lhm.ps1")
}

$VenvPython = Join-Path (Join-Path (Join-Path $RepoRoot ".venv") "Scripts") "python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

if ($OneFolder) {
    $env:PYI_ONEFILE = "0"
    $ExePath = Join-Path (Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert") "cpu-temp-alert.exe"
    $BuildMode = "one-folder"
} else {
    $env:PYI_ONEFILE = "1"
    $ExePath = Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert.exe"
    $BuildMode = "single-file"
}

Write-Host "Installing PyInstaller (if needed)..."
& $Python -m pip install -q "pyinstaller>=6.0.0"

Write-Host "Building with PyInstaller ($BuildMode)..."
& $Python -m PyInstaller $SpecPath --noconfirm --clean

if (-not (Test-Path $ExePath)) {
    throw "Build failed — expected $ExePath"
}

Write-Host ""
Write-Host "Build complete: $ExePath"
if ($OneFolder) {
    Write-Host "Copy config/config.example.json to dist/cpu-temp-alert/config/config.json and edit credentials."
} else {
    Write-Host "Copy config/config.example.json next to the exe:"
    Write-Host "  mkdir (Split-Path $ExePath)/config -Force"
    Write-Host "  Copy-Item config/config.example.json (Split-Path $ExePath)/config/config.json"
}
Write-Host "Run: $ExePath"
