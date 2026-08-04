@echo off


:: should be ran from windows installer (usb)

setlocal

set "UPDATE_PATH=C:\stoic_updates_cache\stoic"
set "STOIC_PATH=C:\stoic"
set "OLD_PATH=C:\stoic_old"

:: getting uid

for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString().Substring(0,8)"') do set UID=%%i
set "OLD_STOIC_PATH=%OLD_PATH%\stoic_%UID%"

:: making a backup of current stoic version

xcopy "%STOIC_PATH%" "%OLD_STOIC_PATH%" /E /I /Y

:: deleting current stoic version

rmdir /s /q "%STOIC_PATH%"

:: copying update to the destination path

xcopy "%UPDATE_PATH%" "%STOIC_PATH%" /E /I /Y




endlocal

