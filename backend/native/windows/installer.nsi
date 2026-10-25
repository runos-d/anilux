Unicode true
!include "MUI2.nsh"
Name "AniLux"
OutFile "@OUTPUT@"
InstallDir "$LOCALAPPDATA\Programs\anilux"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ICON "@DIRECTORY@/icon.ico"
!define MUI_UNICON "@DIRECTORY@/icon.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Russian"
Section "AniLux"
  SetOutPath "$INSTDIR"
  File "@DIRECTORY@/anilux.exe"
  File "@DIRECTORY@/Microsoft.Web.WebView2.Core.dll"
  File "@DIRECTORY@/Microsoft.Web.WebView2.WinForms.dll"
  File "@DIRECTORY@/WebView2Loader.dll"
  File "@DIRECTORY@/*.js"
  File "@DIRECTORY@/app.config.json"
  File "@DIRECTORY@/icon.ico"
  File /nonfatal "@DIRECTORY@/*LICENSE*"
  File /nonfatal "@DIRECTORY@/*NOTICE*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\AniLux"
  CreateShortcut "$SMPROGRAMS\AniLux\AniLux.lnk" "$INSTDIR\anilux.exe"
  CreateShortcut "$DESKTOP\AniLux.lnk" "$INSTDIR\anilux.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "DisplayName" "AniLux"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "DisplayVersion" "@VERSION@"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "UninstallString" '$"$INSTDIR\Uninstall.exe$"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "Publisher" "AniLux"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux" "NoRepair" 1
  ExecWait '$"$INSTDIR\anilux.exe$" --check-runtime' $0
  ${If} $0 != 0
    InitPluginsDir
    SetOutPath "$PLUGINSDIR"
    File "@DIRECTORY@/WebView2Setup.exe"
    ExecWait '$"$PLUGINSDIR\WebView2Setup.exe$" /silent /install' $0
  ${EndIf}
SectionEnd
Section "Uninstall"
  Delete "$DESKTOP\AniLux.lnk"
  Delete "$SMPROGRAMS\AniLux\AniLux.lnk"
  RMDir "$SMPROGRAMS\AniLux"
  Delete "$INSTDIR\anilux.exe"
  Delete "$INSTDIR\Microsoft.Web.WebView2.Core.dll"
  Delete "$INSTDIR\Microsoft.Web.WebView2.WinForms.dll"
  Delete "$INSTDIR\WebView2Loader.dll"
  Delete "$INSTDIR\bridge.js"
  Delete "$INSTDIR\pip-enter.js"
  Delete "$INSTDIR\pip-exit.js"
  Delete "$INSTDIR\app.config.json"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\anilux"
SectionEnd
