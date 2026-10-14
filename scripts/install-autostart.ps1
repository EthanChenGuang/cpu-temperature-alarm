# Register Task Scheduler entry for CPU High Temperature Alert autorun at logon
# Usage (admin): pwsh scripts/install-autostart.ps1
# Dev mode:      pwsh scripts/install-autostart.ps1 -DevMode
param(
    [string]$ExePath = "",
    [switch]$DevMode,
    [switch]$RunAsAdmin,
    [string]$TaskName = "CpuTempAlert"
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    throw "This script must run as Administrator. Right-click PowerShell and choose 'Run as administrator'."
}

$RepoRoot = Split-Path -Parent $PSScriptRoot

if ($DevMode) {
    $VenvPythonw = Join-Path (Join-Path (Join-Path $RepoRoot ".venv") "Scripts") "pythonw.exe"
    if (Test-Path $VenvPythonw) {
        $Target = $VenvPythonw
        $Arguments = "-m src.main"
    } else {
        $Target = "pythonw"
        $Arguments = "-m src.main"
    }
    $WorkingDir = $RepoRoot
} else {
    if (-not $ExePath) {
        $OneFileExe = Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert.exe"
        $OneFolderExe = Join-Path (Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert") "cpu-temp-alert.exe"
        $InstalledExe = Join-Path (Join-Path $env:LOCALAPPDATA "Programs\cpu-temp-alert") "cpu-temp-alert.exe"
        if (Test-Path $InstalledExe) {
            $ExePath = $InstalledExe
        } elseif (Test-Path $OneFileExe) {
            $ExePath = $OneFileExe
        } else {
            $ExePath = $OneFolderExe
        }
    }
    if (-not (Test-Path $ExePath)) {
        throw "Executable not found at $ExePath. Run scripts/build.ps1 first or pass -ExePath."
    }
    $Target = $ExePath
    $Arguments = ""
    $WorkingDir = Split-Path -Parent $ExePath
}

$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Host "Removing existing task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute $Target -Argument $Arguments -WorkingDirectory $WorkingDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

# Limited keeps the tray icon in the normal notification area. Highest (admin)
# hides icons in a separate elevated overflow that most users never see.
$RunLevel = if ($RunAsAdmin) { "Highest" } else { "Limited" }
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel $RunLevel

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "CPU High Temperature Alert — silent tray monitor at logon" | Out-Null

Write-Host "Registered scheduled task '$TaskName'"
Write-Host "  Target:      $Target"
if ($Arguments) { Write-Host "  Arguments:   $Arguments" }
Write-Host "  Working dir: $WorkingDir"
Write-Host "  Run level:   $RunLevel"
if (-not $RunAsAdmin) {
    Write-Host "  Tip: pass -RunAsAdmin only if sensors require elevation (tray icon may hide in overflow)."
}
Write-Host ""
Write-Host "Verify: Get-ScheduledTask -TaskName '$TaskName' | Format-List"
Write-Host "Remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
