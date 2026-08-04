import ctypes;


LOG_PATH       = r"C:\stoic_guardian.log";

# for runner

PYTHON_PATH    = r"C:\Program Files\Python313\python.exe";
WORKING_DIRECTORY  = r"C:\stoic";
RUNNER_COMMAND     = rf'"{PYTHON_PATH}" -m user.main';
#RUNNER_COMMAND = r"C:\Windows\System32\cmd.exe";


# https://learn.microsoft.com/en-us/windows/win32/termserv/wm-wtssession-change

WTS_SESSION_LOGON = 0x5

#    A user has logged on to the session identified by lParam.

WTS_SESSION_LOGOFF = 0x6

#    A user has logged off the session identified by lParam.


# https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nc-winsvc-lphandler_function_ex

SERVICE_CONTROL_SESSIONCHANGE = 0x0000000E

# ...

advapi32 = ctypes.windll.advapi32;
TokenSessionId = 12;

