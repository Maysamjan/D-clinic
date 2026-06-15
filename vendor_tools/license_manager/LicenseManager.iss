; ===========================================================================
;  Zenith Soft License Manager - Inno Setup installer (VENDOR-ONLY)
;  Build the exe first:  pyinstaller --noconfirm LicenseManager.spec
;  Then compile:         "ISCC.exe" LicenseManager.iss
;  Output:               Output\LicenseManager-Setup.exe
;
;  WARNING: This installer is for the SOFTWARE OWNER ONLY. Never distribute it
;  to customers. It does NOT include the private key — after installing, copy
;  license_private\private_key.hex next to the installed LicenseManager.exe.
; ===========================================================================

#define MyAppName        "Zenith Soft License Manager"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Zenith Soft"
#define MyAppExeName     "LicenseManager.exe"

[Setup]
AppId={{B7E2A1C4-9D3F-4A8E-B1C2-7F5E9A0D2C31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Zenith Soft License Manager
DefaultGroupName=Zenith Soft License Manager
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName} {#MyAppVersion}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=LicenseManager-Setup
MinVersion=6.2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Bundle the PyInstaller one-folder output (exe + Qt). The private key and the
; generated_licenses history are intentionally NOT included.
Source: "dist\LicenseManager\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent
