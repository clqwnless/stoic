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
import threading;
import faulthandler;

import sys;



from user_service.config import *;

# for stoic_updater

from user.updater  import get_repo;
from shared.git    import process_commit;
from shared.utils  import read_json, write_json;
from shared.config import PENDING_UPDATE_FILE, UPDATE_FILE, UPDATE_FILE_NAME, UPDATES_CACHE_DIR;

from shared.power  import reboot;

from pathlib       import Path;

from dataclasses import dataclass;

import json;
import os;
import subprocess;
import secrets;
import tempfile;
import shutil;

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

# updater

UPDATE_FILES = [
    "stoic.exe",
    "service.exe"
];
AMOUNT_OF_EXES = 2;



def update_cleanup(update_path):
    update_path = Path(update_path);
    
    if (update_path.exists()):
        shutil.rmtree(update_path);

def _get_update(service_name):
    if (not os.path.exists(PENDING_UPDATE_FILE)):
        return -1, None;
    
    commit = read_json(PENDING_UPDATE_FILE);
    path   = process_commit(get_repo(), UPDATES_CACHE_DIR, commit);
    
    child       = os.listdir(path)[0];
    commit_root = os.path.join(path, child);
    
    # commit checks
    
    exes = [entry.lower() for entry in os.listdir(commit_root) if entry[-4:] == '.exe'];
    
    if (len(exes) != AMOUNT_OF_EXES):
        log(f"stoic updater error: the amount of exes was not expected, expected: {AMOUNT_OF_EXES}, got: {len(exes)}");
        update_cleanup();
        return -2, None;
    
    # set ignores the order of elements
    
    if (set(exes) != set(UPDATE_FILES)):
        log(f"stoic updater error: expected 'exes' in the commit: {UPDATE_FILES}, got: {exes}");
        update_cleanup();
        return -3, None;
    
    # root path check
    
    stoic_root_path     = get_service_path();
    
    # ok (success)
    
    stoic_service_name = get_service_path().name;
    
    return 1, {
        "service_name": service_name,
        "commit_path": commit_root,
        "service_exe_name": str(get_service_path().name),
        "stoic_root_path": str(get_service_path().parent)
    };

# public api

def get_update(service_name):

    ret, update = _get_update(service_name);

    '''
    try:
        ret, update = _get_update(service_name);
    except Exception as e:
        log(f"get_update err: {e}");
        return -5, None;
    else:
        return ret, update;
    '''

def update():
    if (not os.path.exists(UPDATE_FILE)):
        return -1, None;
    
    update = read_json(UPDATE_FILE);
    
    for upd_file in UPDATE_FILES:
        src_path  = os.path.join(update["commit_path"], upd_file);
        
        if (upd_file == "service.exe"):
            dest_path = os.path.join(update["stoic_root_path"], update["service_exe_name"]);
        else:
            dest_path = os.path.join(update["stoic_root_path"], upd_file);
        
        shutil.copy2(src_path, dest_path);
    
    return 0, update;

def is_update_mode():
    if (os.path.exists(UPDATE_FILE)):
        return True;
    return False;

# ...

class ServiceShutdown(Exception):
    pass;

class StoicGuardian(win32serviceutil.ServiceFramework):

    _svc_name_ = "StoicGuardian"
    _svc_display_name_ = "StoicGuardian"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)

        self.args = args;
        self.service_name = args[0];

        self.runners         = dict();
        self.active_sessions = set();

        self.update_check();

    def prepare_update(self, update):
        log("prepare_update");
    
        temp_dir     = Path(tempfile.gettempdir());
        
        # copy service
        
        service_path = Path(sys.argv[0]).resolve();
        dest_path    = temp_dir / service_path.name;
        shutil.copy2(service_path, dest_path);

        # create "UPDATE_FILE" file
        
        upd_file_path = temp_dir / UPDATE_FILE_NAME;
        write_json(upd_file_path, update);
        
        return dest_path;

    def update_check(self):
        log("update_check");
    
        if (not is_update_mode()):
            ret, update = get_update(self.service_name);
            
            log(f"after get_update, ret={ret}, update={update}");
            
            if (ret > 0):
                log("ret > 0");
            
                dest_path = self.prepare_update(update);
                log(f"dest_path: {dest_path}");
                run_exe(dest_path);
                log("run_exe");
                self.shutdown();

    # runner 
    
    def start_runner(self, sid):
        try:
            handle, thread, _, _   = launch_system_to_session(sid, RUNNER_COMMAND, None);
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

    def shutdown(self):
        # signal scm
        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )        
        win32event.SetEvent(self.hWaitStop)

        raise ServiceShutdown()

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
        
        log("SvcDoRun");
        
        while True:
            
            self.guardian();
            
            result = win32event.WaitForSingleObject(
                self.stop_event,
                3000 # waiting 3 sec
            );

            if (result == win32event.WAIT_OBJECT_0):
                break;

# ...

def start_service(service_name):
    subprocess.run(
        ["sc", "start", service_name],
        shell=True
    );

def get_service_path():
    return Path(sys.argv[0]).resolve();

def run_exe(path):
    subprocess.Popen(path);

# ...

def update_stub():
    if (is_update_mode()):
        update = None;
        
        ret, update = update();
        
        '''
        try:
            ret, update = update();
        except:
            pass;
        '''
        
        if (update is None):
            exit(-1)
        
        start_service(update["service_name"]);
        
        exit(0);



if __name__ == "__main__":
    # capturing errors so that debugging is not hell

    sys.excepthook       = exception_hook;
    threading.excepthook = thread_hook;
    faulthandler.enable(open(LOG_PATH, "a", encoding="utf-8"));
    
    update_stub();
    
    log("start");
    
    servicemanager.Initialize();
    servicemanager.PrepareToHostSingle(StoicGuardian);
    servicemanager.StartServiceCtrlDispatcher();

