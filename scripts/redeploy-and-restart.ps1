# Stop all cpu-temp-alert instances, deploy fresh build, restart tray app.
# Requires Administrator (elevated processes must be stopped by elevated shell).
$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run as Administrator: pwsh scripts/redeploy-and-restart.ps1"
}

$InstallDir = "D:\projects\cpu-temp-alert"
$Built = Join-Path $InstallDir "build-work\dist\cpu-temp-alert.exe"
$Target = Join-Path $InstallDir "cpu-temp-alert-v6.20.exe"

Write-Host "Stopping all cpu-temp-alert processes..."
Get-Process | Where-Object { $_.ProcessName -like "cpu-temp-alert*" } | ForEach-Object {
    Write-Host "  Stopping PID $($_.Id) $($_.ProcessName)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3

if (-not (Test-Path $Built)) {
    throw "Build output not found — run build-v6.ps1 first: $Built"
}

Copy-Item -Path $Built -Destination $Target -Force
$sizeMB = [math]::Round((Get-Item $Target).Length / 1MB, 1)
Write-Host "Deployed: $Target ($sizeMB MB)"

Write-Host "Starting tray app..."
Start-Process -FilePath $Target -WorkingDirectory $InstallDir
Start-Sleep -Seconds 2

Get-Process | Where-Object { $_.ProcessName -like "cpu-temp-alert*" } | Format-Table Id, ProcessName -AutoSize
Write-Host "Done."
