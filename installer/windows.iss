#define MyAppName "Producción Litúrgica OBS"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppExeName "ProduccionLiturgicaOBS.exe"

[Setup]
AppId={{EFB4DB79-93C8-4E2B-83BA-8EFC2109B0EA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Comunidad Producción Litúrgica OBS
DefaultDirName={localappdata}\Programs\ProduccionLiturgicaOBS
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=ProduccionLiturgicaOBS-Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Files]
Source: "dist\ProduccionLiturgicaOBS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Los datos y archivos personales se conservan en %LOCALAPPDATA%\ProduccionLiturgicaOBS
