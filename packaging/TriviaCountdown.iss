#ifndef AppVersion
  #error AppVersion must be supplied with /DAppVersion=<version>
#endif

[Setup]
AppId={{F68F8211-DFD3-48C9-90F6-B9D3FA9E9D59}
AppName=Trivia Countdown
AppVersion={#AppVersion}
AppPublisher=Trivia Countdown
DefaultDirName={localappdata}\Programs\Trivia Countdown
DefaultGroupName=Trivia Countdown
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=Trivia-Countdown-{#AppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\Trivia Countdown.exe

[Files]
Source: "..\dist\Trivia Countdown\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Trivia Countdown"; Filename: "{app}\Trivia Countdown.exe"
Name: "{autodesktop}\Trivia Countdown"; Filename: "{app}\Trivia Countdown.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
