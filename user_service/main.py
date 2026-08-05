import win32service;
import win32serviceutil;
import win32event;
import win32api;
import win32con;
import win32process;
import win32security;
import win32profile;
import win32ts;

import servicemanager;
import ctypes;
import time;

import traceback;
import sys;
import threading;
import faulthandler;


from user_service.config import *;


# i hate debugging this service so i decided to create a except hook

def exception_hook(exc_type, exc_value, exc_tb):
    log("".join(traceback.format_exception(exc_type, exc_value, exc_tb)));

def thread_hook(args):
    log("".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)));

def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | {msg}\n")
    except:
        pass

# system

def set_token_session_id(token_handle, session_id):
    session = ctypes.c_uint32(session_id)

    result = advapi32.SetTokenInformation(
        int(token_handle),
        TokenSessionId,
        ctypes.byref(session),
        ctypes.sizeof(session)
    )

    if not result:
        raise ctypes.WinError()

def launch_system_to_session(session_id, command, working_directory=None):

    # getting the token of current process (SYSTEM service)

    current_token = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        win32con.TOKEN_ALL_ACCESS
    )

    # creating a duplicate of the primary token 

    token = win32security.DuplicateTokenEx(
        current_token,
        win32security.SecurityImpersonation,
        win32con.TOKEN_ALL_ACCESS,
        win32security.TokenPrimary
    )


    # changing the session in that token (basically a string)

    set_token_session_id(
        token,
        session_id
    )

    # environment

    env = win32profile.CreateEnvironmentBlock(
        token,
        False
    )


    startup = win32process.STARTUPINFO()
    startup.lpDesktop = "winsta0\\default"

    hProcess, hThread, pid, tid = win32process.CreateProcessAsUser(
        token,
        None,
        command,
        None,
        None,
        False,

        win32con.CREATE_NEW_CONSOLE |
        win32con.CREATE_UNICODE_ENVIRONMENT,

        env,
        working_directory,
        startup
    )
    
    return hProcess, hThread, pid, tid;


class StoicGuardian(win32serviceutil.ServiceFramework):

    _svc_name_ = "StoicGuardian"
    _svc_display_name_ = "StoicGuardian"

    def __init__(self,args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)

        self.runners         = dict();
        self.active_sessions = set();

    # runner 
    
    def start_runner(self, sid):
        try:
            handle, thread, _, _   = launch_system_to_session(sid, RUNNER_COMMAND, WORKING_DIRECTORY);
        except Exception as e:
            log(f"launch_system_to_session err: {e}");
            return;
        
        # removing handle to this thread (not process termination) ; basically, terminating pointer
        
        win32api.CloseHandle(thread)
        
        self.runners[sid] = handle;

    def stop_runner(self, sid):
        if (sid not in self.runners):
            return;
        
        handle = self.runners[sid];
        
        win32process.TerminateProcess(handle, 0);
        win32api.CloseHandle(handle);

        del self.runners[sid];

    # operatoins

    def on_logon(self, sid):
        self.active_sessions.add(sid);
        
        if sid not in self.runners:
            self.start_runner(sid);

    def on_logoff(self, sid):
        self.active_sessions.discard(sid);
        self.stop_runner(sid);

    # guardians

    def guardian(self):
        
        # list to make copy otherwise error while deleting by key in loop
        
        for sid, handle in list(self.runners.items()):

            if (win32event.WaitForSingleObject(handle, 0) == win32con.WAIT_OBJECT_0):

                win32api.CloseHandle(handle);
                
                del self.runners[sid];

                if (sid in self.active_sessions):
                    self.start_runner(sid);

    # ...

    def GetAcceptedControls(self):
        # STOP | SHUTDOWN | PAUSE -> STOP | SHUTDOWN | PAUSE | SESSIONCHANGE
        
        # adds sessionchange
        return super().GetAcceptedControls() | win32service.SERVICE_ACCEPT_SESSIONCHANGE

    def SvcOtherEx(self, control, event_type, data):
        if (control == SERVICE_CONTROL_SESSIONCHANGE):
            
            if (event_type == WTS_SESSION_LOGON):
                self.on_logon(sid=data[0]);
            elif (event_type == WTS_SESSION_LOGOFF):
                self.on_logoff(sid=data[0]);

    def SvcStop(self):
        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        '''
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_,'')
        )
        '''
        # disabling event viewer logs ; if the event viewer service is disabled, this service won't be running
        
        while True:
            
            self.guardian();
            
            result = win32event.WaitForSingleObject(
                self.stop_event,
                3000 # waiting 3 sec
            );

            if (result == win32event.WAIT_OBJECT_0):
                break;


if __name__ == "__main__":
    # capturing errors so that debugging is not hell

    sys.excepthook       = exception_hook;
    threading.excepthook = thread_hook;
    faulthandler.enable(open(LOG_PATH, "a", encoding="utf-8"));
    
    log("start");
    
    servicemanager.Initialize();
    servicemanager.PrepareToHostSingle(StoicGuardian);
    servicemanager.StartServiceCtrlDispatcher();

