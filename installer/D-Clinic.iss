; ===========================================================================
;  D-Clinic - Inno Setup installer script  (Zenith Soft)
;  Produces a professional Windows installer for commercial distribution.
;
;  Build the app first (build.bat or: pyinstaller --noconfirm D-Clinic.spec)
;  so that  dist\D-Clinic\D-Clinic.exe  exists, then compile this script with
;  Inno Setup 6:   "ISCC.exe" installer\D-Clinic.iss
;  Output:         installer\Output\D-Clinic-Setup-1.0.0.exe
; ===========================================================================

#define MyAppName        "D-Clinic"
#define MyAppVersion      "1.0.0"
#define MyAppPublisher    "Zenith Soft"
#define MyAppDescription  "Dental Clinic Management System"
#define MyAppExeName      "D-Clinic.exe"

[Setup]
; A unique identifier for this product (do not reuse for other apps).
AppId={{F357CB13-F98B-431F-B280-F39B0B48341D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDescription}
VersionInfoProductName={#MyAppName}
VersionInfoVersion={#MyAppVersion}

; Install under Program Files and require admin for that.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=admin
DisableProgramGroupPage=yes
DisableDirPage=no

; Branding for the setup wizard and Add/Remove Programs entry.
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

; Where the finished installer is written.
OutputDir=Output
OutputBaseFilename=D-Clinic-Setup-{#MyAppVersion}

; Runs on Windows 8 / 8.1 / 10 / 11 (and Server equivalents).
MinVersion=6.2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Bundle the entire PyInstaller one-folder output (exe + Qt + assets + fonts).
Source: "..\dist\D-Clinic\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Shared, user-writable data folders (database, backups, attachments).
; 'users-modify' lets every Windows account on the clinic PC read/write them.
Name: "{commonappdata}\Zenith Soft\D-Clinic";             Permissions: users-modify
Name: "{commonappdata}\Zenith Soft\D-Clinic\data";        Permissions: users-modify
Name: "{commonappdata}\Zenith Soft\D-Clinic\data\logos";  Permissions: users-modify
Name: "{commonappdata}\Zenith Soft\D-Clinic\backups";     Permissions: users-modify
Name: "{commonappdata}\Zenith Soft\D-Clinic\attachments"; Permissions: users-modify

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}";                Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (created when the task is selected)
Name: "{autodesktop}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
; Offer to launch the app right after installation finishes.
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove only the installed program files. The clinic's data, backups and
; attachments in %PROGRAMDATA% are deliberately PRESERVED on uninstall so a
; reinstall / upgrade never loses patient records.
Type: filesandordirs; Name: "{app}"
