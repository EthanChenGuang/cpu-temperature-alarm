# Post-install hooks for Inno Setup — desktop shortcut, logon autostart, legacy cleanup.
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [switch]$DesktopShortcut,
    [switch]$Autostart
)

$ErrorActionPreference = "Stop"

$AppName = "CPU High Temperature Alert"
$ExeName = "cpu-temp-alert.exe"
$ExePath = Join-Path $InstallDir $ExeName
$LegacyTaskName = "CpuTempAlert"
$StartupShortcutName = "CPU Temp Alert.lnk"

function Set-ShortcutRunAsAdmin {
    param([Parameter(Mandatory = $true)][string]$ShortcutPath)
    $bytes = [System.IO.File]::ReadAllBytes($ShortcutPath)
    $bytes[0x15] = $bytes[0x15] -bor 0x20
    [System.IO.File]::WriteAllBytes($ShortcutPath, $bytes)
}

function New-AdminShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [string]$Arguments = "",
        [string]$Description = $AppName
    )

    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($ShortcutPath)
    $link.TargetPath = $TargetPath
    $link.WorkingDirectory = $WorkingDirectory
    $link.Description = $Description
    if ($Arguments) {
        $link.Arguments = $Arguments
    }
    $link.Save()
    Set-ShortcutRunAsAdmin -ShortcutPath $ShortcutPath
}

if (-not (Test-Path $ExePath)) {
    throw "Installed executable not found: $ExePath"
}

if ($DesktopShortcut) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktop $StartupShortcutName
    New-AdminShortcut `
        -ShortcutPath $shortcutPath `
        -TargetPath $ExePath `
        -WorkingDirectory $InstallDir
}

if ($Autostart) {
    $startupDir = [Environment]::GetFolderPath("Startup")
    $shortcutPath = Join-Path $startupDir $StartupShortcutName
    New-AdminShortcut `
        -ShortcutPath $shortcutPath `
        -TargetPath $ExePath `
        -WorkingDirectory $InstallDir `
        -Arguments "--logon-delay 30"

    Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
}
