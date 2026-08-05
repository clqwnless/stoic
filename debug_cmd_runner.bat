@echo off


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

%SCRIPT_DIR%\user\psexec.exe -i -s C:\Windows\System32\cmd.exe

endlocal

