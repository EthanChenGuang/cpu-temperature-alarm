; CPU High Temperature Alert — Windows installer (Inno Setup 6)
; Build: pwsh scripts/build-installer.ps1

#ifndef AppVersion
  #define AppVersion "6.17.0"
#endif

#ifndef SourceDir
  #define SourceDir "staging"
#endif

#ifndef OutputDir
  #define OutputDir "..\dist"
#endif

#ifndef SetupIconFile
  #define SetupIconFile "..\assets\cpu-temp-alert.ico"
#endif

#define AppName "CPU High Temperature Alert"
#define AppPublisher "CPU Temp Alert"
#define AppExeName "cpu-temp-alert.exe"
#define AppId "{{A7C3E5F1-9B2D-4A6E-8C1F-3D5E7A9B2C4D}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\cpu-temp-alert
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=cpu-temp-alert-setup-{#AppVersion}
SetupIconFile={#SetupIconFile}
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AppMutex=Global\CpuTempAlertSingleton_v1
CloseApplications=yes
RestartApplications=no
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "autostart"; Description: "Start with Windows at logon (recommended)"; GroupDescription: "Startup:"; Flags: checkedonce
Name: "launch"; Description: "Launch {#AppName} after installation"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\config\config.example.json"; DestDir: "{app}\config"; Flags: ignoreversion
Source: "{#SourceDir}\config\config.example.json"; DestDir: "{app}\config"; DestName: "config.json"; Flags: onlyifdoesntexist ignoreversion
Source: "{#SourceDir}\docs\安装与使用说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\installer\post-install.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#SourceDir}\installer\post-uninstall.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Comment: "Monitor CPU/GPU temperatures from the system tray"
Name: "{group}\Edit config.json"; Filename: "notepad.exe"; Parameters: """{app}\config\config.json"""
Name: "{group}\User guide"; Filename: "{app}\安装与使用说明.md"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\installer\post-install.ps1"" -InstallDir ""{app}"" -DesktopShortcut:{code:GetDesktopShortcutFlag} -Autostart:{code:GetAutostartFlag}"; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Creating shortcuts..."
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec; Tasks: launch

[UninstallRun]
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\installer\post-uninstall.ps1"" -InstallDir ""{app}"""; \
  Flags: runhidden waituntilterminated; \
  RunOnceId: "CleanupShortcuts"

[Code]
function BoolToTaskParam(Checked: Boolean): String;
begin
  if Checked then
    Result := 'True'
  else
    Result := 'False';
end;

function GetDesktopShortcutFlag(Param: String): String;
begin
  Result := BoolToTaskParam(WizardIsTaskSelected('desktopicon'));
end;

function GetAutostartFlag(Param: String): String;
begin
  Result := BoolToTaskParam(WizardIsTaskSelected('autostart'));
end;
