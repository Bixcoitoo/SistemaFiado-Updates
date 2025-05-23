; Script Inno Setup para Sistema Fiado
; Salve como installer.iss e abra no Inno Setup Compiler

[Setup]
AppName=Sistema Fiado
AppVersion=1.0.8
DefaultDirName={pf}\SistemaFiado
DefaultGroupName=Sistema Fiado
OutputBaseFilename=Sistema_Fiado_Setup
SetupIconFile=icons\ICONE-LOGO.ico
LicenseFile=LICENSE.txt
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Files]
Source: "dist\Sistema Fiado.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\database"; Permissions: everyone-full
Name: "{app}\database\backups"; Permissions: everyone-full

[Icons]
Name: "{group}\Sistema Fiado"; Filename: "{app}\Sistema Fiado.exe"
Name: "{commondesktop}\Sistema Fiado"; Filename: "{app}\Sistema Fiado.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Run]
Filename: "{app}\Sistema Fiado.exe"; Description: "Iniciar Sistema Fiado"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\database"

[Code]
// Função vazia para manter a seção [Code] válida
procedure CurPageChanged(CurPageID: Integer);
begin
  // Função mantida para futuras implementações
end; 