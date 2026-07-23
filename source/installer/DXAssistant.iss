#ifndef SourceDir
  #error SourceDir must identify the prepared portable application folder
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif
#ifndef AppVersion
  #define AppVersion "0.14.1-beta"
#endif

[Setup]
AppId={{A51F70DA-EF16-48CE-B6EB-A087139AA4B3}
AppName=DX Assistant
AppVersion={#AppVersion}
AppPublisher=DX Assistant project
DefaultDirName={localappdata}\Programs\DX Assistant
DefaultGroupName=DX Assistant
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=DXAssistant-v{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\DXAssistant.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes

[Files]
Source: "{#SourceDir}\DXAssistant.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\config.template.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\RELEASE_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\DXAssistant-v{#AppVersion}-User-Manual.docx"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\DXAssistant-v{#AppVersion}-User-Manual.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\COLLEAGUE_TEST_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DX Assistant"; Filename: "{app}\DXAssistant.exe"; WorkingDir: "{app}"
Name: "{group}\DX Assistant User Manual"; Filename: "{app}\DXAssistant-v{#AppVersion}-User-Manual.pdf"
Name: "{autodesktop}\DX Assistant"; Filename: "{app}\DXAssistant.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\DXAssistant.exe"; Description: "Launch DX Assistant"; Flags: nowait postinstall skipifsilent
