; CountyDataSync Installer Script
; For use with Nullsoft Scriptable Install System (NSIS)

; Define application name and version
!define APPNAME "CountyDataSync"
!define VERSION "1.0.0"
!define PUBLISHER "County Data Services"

; General settings
Name "${APPNAME} ${VERSION}"
OutFile "${APPNAME}-${VERSION}-setup.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "Install_Dir"
RequestExecutionLevel admin

; Pages
!include "MUI2.nsh"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; File section
Section "Install"
    SetOutPath $INSTDIR
    
    ; Main executable
    File "..\dist\CountyDataSync.exe"
    
    ; Documentation
    File "..\README.md"
    File "..\INSTALLATION.md"
    File "..\PACKAGING.txt"
    
    ; Configuration
    File "..\config.py"
    File "..\.env.example"
    
    ; Create directories
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\output"
    CreateDirectory "$INSTDIR\data"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\CountyDataSync.exe"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\CountyDataSync.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\${APPNAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
    
    ; Write estimated size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" "$0"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\CountyDataSync.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\INSTALLATION.md"
    Delete "$INSTDIR\PACKAGING.txt"
    Delete "$INSTDIR\config.py"
    Delete "$INSTDIR\.env.example"
    Delete "$INSTDIR\uninstall.exe"
    
    ; Remove directories (except logs and output if they contain files)
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    RMDir "$INSTDIR\logs"
    RMDir "$INSTDIR\output"
    RMDir "$INSTDIR\data"
    RMDir "$INSTDIR"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${APPNAME}"
    
    ; Remove desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"
SectionEnd
