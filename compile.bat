@echo off


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

cd "%SCRIPT_DIR%"

:main

cls
echo.
echo For compiling user-service consider using user_service.bat
echo.
echo  - [0] Compile User
echo  - [1] Compile Verifier
echo.

set "choice="
set /p "choice=>>> "

if not defined choice (
    goto main
)

if %choice% equ 0 (
    call :compile_user
) else if %choice% equ 1 (
    call :compile_verifier
) else if /i "%choice%" == "x" (
    exit /b 0
)

goto main

:compile_user

cd "%SCRIPT_DIR%"
call Scripts\activate.bat > nul 2>&1

python.exe -m nuitka user\main.py --onefile --remove-output --clean-cache=all --output-filename=stoic

pause
exit /b 0

:compile_verifier

cd "%SCRIPT_DIR%"
call Scripts\activate.bat > nul 2>&1

python.exe -m nuitka verifier\main.py --onefile --remove-output --clean-cache=all --output-filename=verifier

pause
exit /b 0



endlocal

