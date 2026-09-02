@echo off


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "SERVICE_NAME=StoicGuardian"

set "SERVICE_EXE_NAME=stoic_guardian"
set "SERVICE_PATH=%SCRIPT_DIR%\%SERVICE_EXE_NAME%.exe"

:main

cls
echo.
echo  - [0] Compile
echo  - [1] Install
echo  - [2] Delete
echo  - [3] Stop
echo  - [4] Start
echo  - [5] Install in SafeMode (so that the service can't be bypassed)
echo  - [6] Reset env values
echo.

set "choice="
set /p "choice=>>> "

if not defined choice (
    goto main
)

if %choice% equ 0 (
    call :compile
) else if %choice% equ 1 (
    call :install
) else if %choice% equ 2 (
    call :delete
) else if %choice% equ 3 (
    call :stop
) else if %choice% equ 4 (
    call :start
) else if %choice% equ 5 (
	call :install_in_safe_mode
) else if %choice% equ 6 (
    call :reset_env_values
) else if /i "%choice%" == "x" (
    exit /b 0
)

goto main



:compile

cd "%SCRIPT_DIR%"
call Scripts\activate.bat > nul 2>&1

python.exe -m nuitka user_service\main.py --onefile --remove-output --clean-cache=all --output-filename="%SERVICE_EXE_NAME%" --nofollow-import-to=dropbox.*

pause
exit /b 0


:install

sc create "%SERVICE_NAME%" binPath="%SERVICE_PATH%" start=auto obj= LocalSystem

echo.
echo Don't forget to protect the service using the init.acl_protect_data file
echo.

pause
exit /b 0


:stop

sc stop %SERVICE_NAME%

pause
exit /b 0


:delete

sc stop   %SERVICE_NAME%
sc delete %SERVICE_NAME%

reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SafeBoot\Minimal\%SERVICE_NAME%" /f
reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\%SERVICE_NAME%" /f

pause
exit /b 0


:start

sc start %SERVICE_NAME%

pause
exit /b 0


:install_in_safe_mode

reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SafeBoot\Minimal\%SERVICE_NAME%" /ve /t REG_SZ /d Service /f
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\%SERVICE_NAME%" /ve /t REG_SZ /d Service /f

pause
exit /b 0

:reset_env_values

echo Resetting STOIC_GUARDIAN_ON_RESUME
setx STOIC_GUARDIAN_ON_RESUME 0

pause
exit /b 0

endlocal

