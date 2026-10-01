#ifndef AppVersion
  #error AppVersion must be supplied by scripts/build_installer.py
#endif
#ifndef ProjectDir
  #error ProjectDir must be supplied by scripts/build_installer.py
#endif
#ifndef PayloadDir
  #error PayloadDir must be supplied by scripts/build_installer.py
#endif

[Setup]
AppId={{F8674615-7211-4D03-A149-7BAEAA66D593}
AppName=Hangullo
AppVersion=v{#AppVersion}
AppVerName=Hangullo v{#AppVersion}
AppPublisher=Hangullo Project
AppComments=한국어 기반 프로그래밍 언어 Hangullo의 통합 개발 환경입니다.
DefaultDirName={localappdata}\Programs\Hangullo
DefaultGroupName=Hangullo
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName=Hangullo v{#AppVersion}
UninstallDisplayIcon={app}\Hangullo.exe
LicenseFile={#ProjectDir}\LICENSE
SetupIconFile={#ProjectDir}\assets\icon\Hangullo_Logo2.ico
OutputDir={#ProjectDir}\dist
OutputBaseFilename=Hangullo-v{#AppVersion}-Setup
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
ChangesAssociations=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕 화면 바로가기 만들기"; GroupDescription: "추가 바로가기:"; Flags: unchecked
Name: "fileassoc"; Description: ".hg 파일을 Hangullo IDE와 연결"; GroupDescription: "파일 연결:"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectDir}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Hangullo"; Filename: "{app}\Hangullo.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Hangullo"; Filename: "{app}\Hangullo.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\.hg"; ValueType: string; ValueName: ""; ValueData: "HangulloFile"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\.hg\OpenWithProgids"; ValueType: string; ValueName: "HangulloFile"; ValueData: ""; Flags: uninsdeletevalue uninsdeletekeyifempty; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\HangulloFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\Hangullo.exe"",0"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\HangulloFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Hangullo.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: fileassoc

[Run]
Filename: "{app}\Hangullo.exe"; Description: "Hangullo 실행"; Flags: postinstall nowait skipifsilent

[Code]
const
  AssociationBackupKey = 'Software\Hangullo\InstallerBackup\F8674615-7211-4D03-A149-7BAEAA66D593';
  HangulloAssociationKey = 'Software\Classes\.hg';

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExistingMarker: string;
  ExistingProgId: string;
begin
  if (CurStep = ssInstall) and WizardIsTaskSelected('fileassoc') then
  begin
    if not RegQueryStringValue(HKCU, AssociationBackupKey, 'HadPrevious', ExistingMarker) then
    begin
      if RegQueryStringValue(HKCU, HangulloAssociationKey, '', ExistingProgId) then
      begin
        RegWriteStringValue(HKCU, AssociationBackupKey, 'HadPrevious', '1');
        RegWriteStringValue(HKCU, AssociationBackupKey, 'PreviousProgId', ExistingProgId);
      end
      else
        RegWriteStringValue(HKCU, AssociationBackupKey, 'HadPrevious', '0');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  BackupMarker: string;
  PreviousProgId: string;
  CurrentProgId: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegQueryStringValue(HKCU, AssociationBackupKey, 'HadPrevious', BackupMarker) then
    begin
      if RegQueryStringValue(HKCU, HangulloAssociationKey, '', CurrentProgId) and
         (CurrentProgId = 'HangulloFile') then
      begin
        if (BackupMarker = '1') and
           RegQueryStringValue(HKCU, AssociationBackupKey, 'PreviousProgId', PreviousProgId) then
          RegWriteStringValue(HKCU, HangulloAssociationKey, '', PreviousProgId)
        else
          RegDeleteValue(HKCU, HangulloAssociationKey, '');
      end;
      RegDeleteKeyIncludingSubkeys(HKCU, AssociationBackupKey);
    end;
  end;
end;