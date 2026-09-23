#define AppVersion "1.0.1"

[Setup]
AppId={{1906af90-0d38-475a-9cba-ae19e7aee8ef}
AppName=見積管理システム
AppVersion={#AppVersion}
AppVerName=見積管理システム {#AppVersion}
DefaultDirName={localappdata}\Programs\EstimateDesktop
DefaultGroupName=見積管理システム
PrivilegesRequired=lowest
OutputDir=..\deliverables
OutputBaseFilename=EstimateDesktop-Setup-{#AppVersion}
SetupIconFile=..\desktop-assets\Estimate2.ico
UninstallDisplayIcon={app}\Estimate2.exe
WizardStyle=modern
MinVersion=10.0
ArchitecturesAllowed=x64compatible
Compression=lzma2
SolidCompression=yes
CloseApplications=yes

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成"; GroupDescription: "ショートカット:"; Flags: unchecked

[Files]
Source: "..\deliverables\desktop\Estimate2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.sqlite3,*.db,.env"

[Icons]
Name: "{group}\見積管理システム"; Filename: "{app}\Estimate2.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Estimate2.exe"
Name: "{userdesktop}\見積管理システム"; Filename: "{app}\Estimate2.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Estimate2.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Estimate2.exe"; Description: "見積管理システムを起動"; Flags: nowait postinstall skipifsilent
