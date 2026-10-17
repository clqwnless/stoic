from shared.time_utils import get_current_time;
from shared.config     import SYSTEM_PROC_PAIRS;
from shared.cmd        import pause;


import psutil;
import sys;
import json;


SLEEP_INTERVAL = 0.1; # not to overload the processor


def get_runned_processes():
    process_list = list();
    
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            process_list.append((proc.info['name'], proc.exe(), proc.info['pid'], proc.info['username']));
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue;
    
    return process_list;

def kill_proc(pid):
    try:
        proc = psutil.Process(pid);
        proc.kill();
    except:
        return;

def is_nt_system(user_name):
    if (user_name == "NT AUTHORITY\\SYSTEM"):
        return True;
    return False;

def procmon(allowed_proc: list[str]):
    current_time   = get_current_time(); 
    
    # делаем одним регистром (по сути приводим к общему знаменателю иначе proc in allowed_proc может не работать)
    allowed_proc = [proc.lower() for proc in allowed_proc];
    
    while True:
        # если unix_until is None то там ожидается что main убьёт этот процесс сам короче (мы юзаем модуль multiprocessing)
        
        runned_processes = get_runned_processes();

        for proc_name, proc_exe, pid, user_name in runned_processes:            
            # skipping all programs runned by admin
            
            if (is_nt_system(user_name)):
                continue;
            
            # skipping all system processes
            
            proc_pair = [proc_name, proc_exe];

            if (proc_pair in SYSTEM_PROC_PAIRS):
                continue;
            
            # skipping all allowed processes
            
            if (proc_exe.lower() in allowed_proc):
                continue;
            
            # (runned as not nt\authority) & (is not a system proc) & (is not an allowed proc)
            
            kill_proc(pid);
        
        current_time = get_current_time();
        time.sleep(SLEEP_INTERVAL);


