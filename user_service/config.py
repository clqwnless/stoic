from shared.config import PATH, ROOT_PATH;

import ctypes;

# paths

LOG_PATH = PATH(ROOT_PATH, "stoic_guardian.log");
USER_EXE = PATH(ROOT_PATH, "stoic.exe");

# command

RUNNER_COMMAND     = f'"{USER_EXE}"';

# https://learn.microsoft.com/en-us/windows/win32/termserv/wm-wtssession-change

WTS_SESSION_LOGON = 0x5

#    A user has logged on to the session identified by lParam.

WTS_SESSION_LOGOFF = 0x6

#    A user has logged off the session identified by lParam.

# https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nc-winsvc-lphandler_function_ex

SERVICE_CONTROL_SESSIONCHANGE = 0x0000000E

# ...

advapi32       = ctypes.windll.advapi32;
TokenSessionId = 12;

