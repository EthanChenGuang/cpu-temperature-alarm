# Build and deploy cpu-temp-alert to D:\projects\cpu-temp-alert
$ErrorActionPreference = "Stop"

$RepoRootWsl = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Guang\AppData\Local\Programs\Python\Python313\python.exe"
$InstallDir = "D:\projects\cpu-temp-alert"
$BuildWork = Join-Path $InstallDir "build-work"
$LogPath = Join-Path $InstallDir "build-log-v6.txt"
$Target = Join-Path $InstallDir "cpu-temp-alert-v6.20.exe"

Write-Host "Stopping running instances..."
Get-Process -Name "cpu-temp-alert*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Syncing sources to native Windows path: $BuildWork"
if (Test-Path $BuildWork) {
    Remove-Item -Recurse -Force $BuildWork
}
New-Item -ItemType Directory -Force -Path $BuildWork | Out-Null

$CopyItems = @(
    "src",
    "scripts",
    "assets",
    "vendor",
    "config",
    "docs",
    "requirements.txt",
    "cpu-temp-alert.spec"
)
foreach ($item in $CopyItems) {
    $source = Join-Path $RepoRootWsl $item
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination (Join-Path $BuildWork $item) -Recurse -Force
    }
}

Set-Location $BuildWork

Write-Host "Installing dependencies..."
& $Py -m pip install -q -r requirements.txt "pyinstaller>=6.0.0"

Write-Host "Generating application icon..."
& $Py -c "from src.ui.icon_renderer import generate_app_icon_file; generate_app_icon_file(r'$BuildWork/assets/cpu-temp-alert.ico')"

$env:PYI_ONEFILE = "1"
Write-Host "Building with PyInstaller (single-file, native path)..."
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$buildOutput = & $Py -m PyInstaller (Join-Path $BuildWork "cpu-temp-alert.spec") --noconfirm --clean 2>&1
$pyExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
$buildOutput | Out-File -FilePath $LogPath -Encoding utf8
$buildOutput | Select-Object -Last 12 | ForEach-Object { Write-Host $_ }

if ($pyExit -ne 0) {
    throw "PyInstaller failed with exit code $pyExit"
}

$Built = Join-Path $BuildWork "dist\cpu-temp-alert.exe"
if (-not (Test-Path $Built)) {
    throw "Build output not found: $Built"
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path $Built -Destination $Target -Force

$GuideSource = Join-Path $BuildWork "docs\安装与使用说明.md"
$GuideTarget = Join-Path $InstallDir "安装与使用说明.md"
$GuideBackup = Join-Path $RepoRootWsl "安装与使用说明.md"
if (Test-Path $GuideSource) {
    Copy-Item -Path $GuideSource -Destination $GuideTarget -Force
    Copy-Item -Path $GuideSource -Destination $GuideBackup -Force
    Write-Host "Guide copied: $GuideTarget"
    Write-Host "Guide backup: $GuideBackup"
}

$sizeMB = [math]::Round((Get-Item $Target).Length / 1MB, 1)
Write-Host ""
Write-Host "Deployed: $Target ($sizeMB MB)"

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "CPU Temp Alert.lnk"
$shell = New-Object -ComObject WScript.Shell
if (Test-Path $ShortcutPath) {
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $Target
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "CPU High Temperature Alert v6.20"
    $shortcut.Save()
    $bytes = [System.IO.File]::ReadAllBytes($ShortcutPath)
    $bytes[0x15] = $bytes[0x15] -bor 0x20
    [System.IO.File]::WriteAllBytes($ShortcutPath, $bytes)
    Write-Host "Desktop shortcut updated: $ShortcutPath"
} else {
    Write-Host "No desktop shortcut found — create manually pointing to $Target"
}

$StartupShortcut = Join-Path ([Environment]::GetFolderPath("Startup")) "CPU Temp Alert.lnk"
$startup = $shell.CreateShortcut($StartupShortcut)
$startup.TargetPath = $Target
$startup.Arguments = "--logon-delay 30"
$startup.WorkingDirectory = $InstallDir
$startup.Description = "CPU High Temperature Alert v6.20"
$startup.Save()
$startupBytes = [System.IO.File]::ReadAllBytes($StartupShortcut)
$startupBytes[0x15] = $startupBytes[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes($StartupShortcut, $startupBytes)
Write-Host "Startup shortcut updated: $StartupShortcut (Run as administrator)"

Write-Host "Done."

Write-Host ""
Write-Host "Running WhatsApp self-test..."
Set-Location $InstallDir
Remove-Item whatsapp-test-result.txt -ErrorAction SilentlyContinue
Start-Process -FilePath $Target -ArgumentList "--test-whatsapp" -Verb RunAs -Wait
if (Test-Path (Join-Path $InstallDir "whatsapp-test-result.txt")) {
    Get-Content (Join-Path $InstallDir "whatsapp-test-result.txt")
} else {
    Write-Host "WhatsApp test result file not found — check cpu-temp-alert.log"
}
if (Test-Path (Join-Path $InstallDir "cpu-temp-alert.log")) {
    Get-Content (Join-Path $InstallDir "cpu-temp-alert.log") -Tail 3
}
