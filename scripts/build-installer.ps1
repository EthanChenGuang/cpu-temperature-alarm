# Build CPU High Temperature Alert Windows installer (Inno Setup).
# Usage:
#   pwsh scripts/build-installer.ps1
#   pwsh scripts/build-installer.ps1 -SkipBuild
#   pwsh scripts/build-installer.ps1 -AppVersion 6.18.0
param(
    [string]$AppVersion = "6.20.0",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$IssFile = Join-Path $RepoRoot "installer\cpu-temp-alert.iss"
$DistDir = Join-Path $RepoRoot "dist"
$NativeDist = Join-Path $env:TEMP "cpu-temp-alert-installer-output"
$BuiltExe = Join-Path $DistDir "cpu-temp-alert.exe"

function Find-InnoSetupCompiler {
    $Candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:LocalAppData}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $Candidates) {
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

function Reset-StagingDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (Test-Path $Path) {
        Remove-Item -Recurse -Force $Path
    }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

Write-Host "=== CPU High Temperature Alert — Installer Build ==="
Write-Host ""

if (-not $SkipBuild) {
    Write-Host "Building application executable..."
    & (Join-Path $RepoRoot "scripts\build.ps1")
    Write-Host ""
}

if (-not (Test-Path $BuiltExe)) {
    throw "Built executable not found at $BuiltExe. Run without -SkipBuild or build manually."
}

$iconSource = Join-Path $RepoRoot "assets\cpu-temp-alert.ico"
if (-not (Test-Path $iconSource)) {
    $VenvPython = Join-Path (Join-Path (Join-Path $RepoRoot ".venv") "Scripts") "python.exe"
    if (-not (Test-Path $VenvPython)) {
        $VenvPython = "python"
    }
    Write-Host "Generating application icon..."
    & $VenvPython -c "from src.ui.icon_renderer import generate_app_icon_file; generate_app_icon_file(r'$iconSource')"
}

Write-Host "Staging installer payload..."
$NativeStaging = Join-Path $env:TEMP "cpu-temp-alert-installer-staging"
Reset-StagingDirectory -Path $NativeStaging

$NativeConfig = Join-Path $NativeStaging "config"
$NativeDocs = Join-Path $NativeStaging "docs"
$NativeInstaller = Join-Path $NativeStaging "installer"
foreach ($dir in @($NativeConfig, $NativeDocs, $NativeInstaller)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Copy-Item -Path $BuiltExe -Destination (Join-Path $NativeStaging "cpu-temp-alert.exe") -Force
Copy-Item -Path (Join-Path $RepoRoot "config\config.example.json") -Destination (Join-Path $NativeConfig "config.example.json") -Force

$GuideCandidates = @(
    (Join-Path $RepoRoot "docs\安装与使用说明.md"),
    (Join-Path $RepoRoot "安装与使用说明.md")
)
$GuideCopied = $false
foreach ($guide in $GuideCandidates) {
    if (Test-Path $guide) {
        Copy-Item -Path $guide -Destination (Join-Path $NativeDocs "安装与使用说明.md") -Force
        $GuideCopied = $true
        break
    }
}
if (-not $GuideCopied) {
    Write-Host "Warning: user guide not found — installer will ship without 安装与使用说明.md"
}

Copy-Item -Path (Join-Path $RepoRoot "installer\post-install.ps1") -Destination (Join-Path $NativeInstaller "post-install.ps1") -Force
Copy-Item -Path (Join-Path $RepoRoot "installer\post-uninstall.ps1") -Destination (Join-Path $NativeInstaller "post-uninstall.ps1") -Force
Copy-Item -Path $iconSource -Destination (Join-Path $NativeStaging "cpu-temp-alert.ico") -Force
$NativeIcon = Join-Path $NativeStaging "cpu-temp-alert.ico"

$Iscc = Find-InnoSetupCompiler
if (-not $Iscc) {
    Write-Host "Inno Setup 6 not found — attempting install via winget..."
    winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements | Out-Host
    $Iscc = Find-InnoSetupCompiler
}
if (-not $Iscc) {
    throw @"
Inno Setup 6 not found. Install from https://jrsoftware.org/isinfo.php
Expected ISCC.exe at one of:
  ${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe
  $env:ProgramFiles\Inno Setup 6\ISCC.exe
Then re-run: pwsh scripts/build-installer.ps1
"@
}

New-Item -ItemType Directory -Force -Path $NativeDist | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

Write-Host "Compiling installer with Inno Setup..."
Write-Host "  ISCC: $Iscc"
Write-Host "  Version: $AppVersion"
Write-Host "  Staging: $NativeStaging"
Write-Host "  Output: $NativeDist"
Set-Location $RepoRoot
& $Iscc "/DAppVersion=$AppVersion" "/DSourceDir=$NativeStaging" "/DOutputDir=$NativeDist" "/DSetupIconFile=$NativeIcon" $IssFile

$NativeInstallerPath = Join-Path $NativeDist "cpu-temp-alert-setup-$AppVersion.exe"
$InstallerPath = Join-Path $DistDir "cpu-temp-alert-setup-$AppVersion.exe"
if (-not (Test-Path $NativeInstallerPath)) {
    throw "Installer build failed — expected $NativeInstallerPath"
}

Copy-Item -Path $NativeInstallerPath -Destination $InstallerPath -Force

$sizeMB = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 1)
Write-Host ""
Write-Host "Installer ready: $InstallerPath ($sizeMB MB)"
Write-Host ""
Write-Host "Install on target machine:"
Write-Host "  Double-click cpu-temp-alert-setup-$AppVersion.exe"
Write-Host "  Default location: %LOCALAPPDATA%\Programs\cpu-temp-alert\"
Write-Host "  Edit config after install: notepad %LOCALAPPDATA%\Programs\cpu-temp-alert\config\config.json"
