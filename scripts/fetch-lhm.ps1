# Download and extract LibreHardwareMonitor v0.9.6 DLLs to vendor/LibreHardwareMonitor/
# Idempotent — safe to re-run.
$ErrorActionPreference = "Stop"

$Version = "0.9.6"
$ZipUrl = "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v$Version/LibreHardwareMonitor.zip"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Dest = Join-Path (Join-Path $RepoRoot "vendor") "LibreHardwareMonitor"

New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "lhm-fetch-$Version"
if (Test-Path $TempDir) {
    Remove-Item -Recurse -Force $TempDir
}
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

$ZipPath = Join-Path $TempDir "LibreHardwareMonitor.zip"
Write-Host "Downloading LibreHardwareMonitor v$Version from $ZipUrl"
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing

Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

$LibDll = Get-ChildItem -Path $TempDir -Recurse -Filter "LibreHardwareMonitorLib.dll" -File |
    Select-Object -First 1
if (-not $LibDll) {
    throw "LibreHardwareMonitorLib.dll not found in extracted archive"
}

$DllSource = Get-ChildItem -Path $LibDll.DirectoryName -Filter "*.dll" -File
if ($DllSource.Count -eq 0) {
    throw "No DLL files found alongside LibreHardwareMonitorLib.dll"
}

foreach ($dll in $DllSource) {
    Copy-Item -Path $dll.FullName -Destination $Dest -Force
}

Write-Host "Copied $($DllSource.Count) DLL(s) to $Dest"
Remove-Item -Recurse -Force $TempDir
