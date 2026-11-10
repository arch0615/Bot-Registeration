; Inno Setup script for R-Bot.
; Produces: dist\Setup.exe (one Setup.exe installer).
; Target:   Windows 10 / 11, 64-bit, per-user install (no admin required).
;
; Compile with:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; The build.ps1 script runs ISCC after PyInstaller succeeds.

#define AppName       "R-Bot"
#define AppPublisher  "QA Automation"
#define AppVersion    "1.0.0"
#define AppExeName    "R-Bot.exe"
#define SourceDir     "dist\R-Bot"

[Setup]
AppId={{B6A3F0B1-6E4C-4F3B-9B1A-6F2D5D2E3A10}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
; Per-user install → no UAC prompt
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UsePreviousAppDir=yes
DefaultGroupName={#AppName}
DisableProgramGroupPage=auto
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=dist
OutputBaseFilename=Setup
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
ShowLanguageDialog=no
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Main app binary + the whole PyInstaller One-Folder output
Source: "{#SourceDir}\{#AppExeName}";              DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\*";                           DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Chromium (copied in next to the exe by build.ps1 BEFORE ISCC runs)
Source: "{#SourceDir}\playwright-browsers\*";       DestDir: "{app}\playwright-browsers"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}";                      Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}";            Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";                Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Dirs]
; Per-user writable data dirs (created even if the app is launched before the first run)
Name: "{localappdata}\{#AppName}";                 Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\UserData";        Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\UserData\IDs";    Flags: uninsneveruninstall
Name: "{localappdata}\{#AppName}\UserData\logs";   Flags: uninsneveruninstall

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('R-Bot requires 64-bit Windows 10 (build 1809) or newer.', mbCriticalError, MB_OK);
    Result := False;
    Exit;
  end;
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\{#AppName}');
    if DirExists(DataDir) then
    begin
      if MsgBox('Do you also want to delete your R-Bot user data (settings, history, IDs, logs) at ' + DataDir + ' ?',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
