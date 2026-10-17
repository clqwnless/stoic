@echo off


setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

cd "%SCRIPT_DIR%"

python.exe -m nuitka user/mon/mon.py --onefile --remove-output --clean-cache=all --output-filename=mon --nofollow-import-to=dropbox.team_log

endlocal

