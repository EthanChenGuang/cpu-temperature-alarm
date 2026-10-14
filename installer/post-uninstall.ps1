# Post-uninstall cleanup — remove shortcuts and legacy scheduled tasks.
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Continue"

$ShortcutName = "CPU Temp Alert.lnk"
$LegacyTaskName = "CpuTempAlert"

function Remove-ShortcutIfExists {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $path = Join-Path $Directory $ShortcutName
    if (Test-Path $path) {
        Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
    }
}

Remove-ShortcutIfExists -Directory ([Environment]::GetFolderPath("Desktop"))
Remove-ShortcutIfExists -Directory ([Environment]::GetFolderPath("Startup"))

Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
