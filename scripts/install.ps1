# Build, install, create desktop shortcut, and register admin autostart.
# Usage (run PowerShell as Administrator):
#   pwsh scripts/install.ps1
param(
    [switch]$SkipBuild,
    [switch]$OneFolder,
    [switch]$NoAutostart,
    [switch]$NoDesktopShortcut,
    [string]$InstallDir = "",
    [string]$TaskName = "CpuTempAlert"
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Set-ShortcutRunAsAdmin {
    param([Parameter(Mandatory = $true)][string]$ShortcutPath)
    $bytes = [System.IO.File]::ReadAllBytes($ShortcutPath)
    $bytes[0x15] = $bytes[0x15] -bor 0x20
    [System.IO.File]::WriteAllBytes($ShortcutPath, $bytes)
}

function New-DesktopShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [string]$Description = "CPU High Temperature Alert"
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.Description = $Description
    $shortcut.Save()
    Set-ShortcutRunAsAdmin -ShortcutPath $ShortcutPath
}

if (-not (Test-Administrator)) {
    throw "Run PowerShell as Administrator: pwsh scripts/install.ps1"
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $InstallDir) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\cpu-temp-alert"
}

Write-Host "=== CPU High Temperature Alert — Install ==="
Write-Host ""

if (-not $SkipBuild) {
    $buildArgs = @()
    if ($OneFolder) {
        $buildArgs += "-OneFolder"
    }
    Write-Host "Building executable..."
    & (Join-Path $RepoRoot "scripts" "build.ps1") @buildArgs
    Write-Host ""
}

if ($OneFolder) {
    $BuiltExe = Join-Path (Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert") "cpu-temp-alert.exe"
} else {
    $BuiltExe = Join-Path (Join-Path $RepoRoot "dist") "cpu-temp-alert.exe"
}

if (-not (Test-Path $BuiltExe)) {
    throw "Built executable not found at $BuiltExe. Run without -SkipBuild or check build output."
}

Write-Host "Installing to $InstallDir ..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path $BuiltExe -Destination (Join-Path $InstallDir "cpu-temp-alert.exe") -Force

$InstalledExe = Join-Path $InstallDir "cpu-temp-alert.exe"
$ConfigDir = Join-Path $InstallDir "config"
$ConfigPath = Join-Path $ConfigDir "config.json"
$ExampleConfig = Join-Path (Join-Path $RepoRoot "config") "config.example.json"

New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
if (-not (Test-Path $ConfigPath)) {
    if (Test-Path $ExampleConfig) {
        Copy-Item -Path $ExampleConfig -Destination $ConfigPath
        Write-Host "Created config: $ConfigPath (edit WhatsApp credentials before relying on alerts)"
    } else {
        Write-Host "Warning: config.example.json missing — create $ConfigPath manually"
    }
} else {
    Write-Host "Keeping existing config: $ConfigPath"
}

if (-not $NoDesktopShortcut) {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $Desktop "CPU Temp Alert.lnk"
    New-DesktopShortcut `
        -TargetPath $InstalledExe `
        -WorkingDirectory $InstallDir `
        -ShortcutPath $ShortcutPath
    Write-Host "Desktop shortcut (Run as administrator): $ShortcutPath"
}

if (-not $NoAutostart) {
    Write-Host "Registering logon autostart with administrator privileges..."
    & (Join-Path $RepoRoot "scripts" "install-autostart.ps1") `
        -ExePath $InstalledExe `
        -RunAsAdmin `
        -TaskName $TaskName
}

Write-Host ""
Write-Host "Install complete."
Write-Host "  Executable: $InstalledExe"
Write-Host "  Config:     $ConfigPath"
if (-not $NoAutostart) {
    Write-Host "  Autostart:  Task '$TaskName' at logon (highest privileges)"
}
Write-Host ""
Write-Host "Next: edit config.json with CallMeBot credentials, then launch from the desktop shortcut or reboot to test autostart."
