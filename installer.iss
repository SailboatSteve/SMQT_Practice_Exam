[Setup]
AppName=SMQT Practice Test
AppVersion=1.0
DefaultDirName={autopf}\SMQT Practice Test
DefaultGroupName=SMQT Practice Test
OutputDir=installer
OutputBaseFilename=SMQT_Practice_Test_Setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\SMQT_Practice.exe
WizardStyle=modern

[Files]
Source: "dist\SMQT_Practice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "download_questions.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SMQT Practice Test"; Filename: "{app}\SMQT_Practice.exe"
Name: "{commondesktop}\SMQT Practice Test"; Filename: "{app}\SMQT_Practice.exe"

[Run]
; Download latest questions
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\download_questions.ps1"" ""{app}"""; \
    StatusMsg: "Downloading latest questions..."; Flags: runhidden
; Launch the application
Filename: "{app}\SMQT_Practice.exe"; Description: "Launch SMQT Practice Test"; Flags: postinstall nowait

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
