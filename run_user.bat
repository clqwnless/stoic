@echo off


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

setx "STOIC_ROOT_PATH" "%SCRIPT_DIR%"

cd "%SCRIPT_DIR%"

start "" cmd.exe /c "python.exe -m user.main"

endlocal

