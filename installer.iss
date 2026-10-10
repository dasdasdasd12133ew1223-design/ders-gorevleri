#define SourceDir "build\installer-source\DersGorevleri"

[Setup]
AppId={{8C7FC4C1-3C1D-4E98-A52D-C68728A14C19}
AppName=Ders Görevleri
AppVersion=1.0.0
AppPublisher=YKS Dostu
DefaultDirName={localappdata}\Programs\DersGorevleri
DefaultGroupName=Ders Görevleri
UninstallDisplayIcon={app}\DersGorevleri.exe
SetupIconFile={#SourceDir}\_internal\assets\logo.ico
OutputDir=site\downloads
OutputBaseFilename=Ders-Gorevleri-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
VersionInfoProductName=Ders Görevleri
VersionInfoProductVersion=1.0.0

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek kısayollar:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Ders Görevleri"; Filename: "{app}\DersGorevleri.exe"; IconFilename: "{app}\_internal\assets\logo.ico"
Name: "{autodesktop}\Ders Görevleri"; Filename: "{app}\DersGorevleri.exe"; IconFilename: "{app}\_internal\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\DersGorevleri.exe"; Description: "Ders Görevleri uygulamasını başlat"; Flags: postinstall nowait skipifsilent
