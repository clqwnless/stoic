@echo off

:: should be ran as administrator
:: the goal of the script is to be able to run the stoic as a nt authority\system without installing the service


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "TEMP_FILE=%TEMP%\stoic_runner_temp.bat"

call :create_temp_runner

%SCRIPT_DIR%\user\psexec.exe -i -s -d %TEMP_FILE%

endlocal

exit /b 0

:create_temp_runner

echo cd %SCRIPT_DIR% > %TEMP_FILE%
echo python -m user.main >> %TEMP_FILE%

exit /b 0
