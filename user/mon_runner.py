from shared.config import MON_EXE_PATH, DISABLE_WHITELIST_ENFORCER;

import subprocess;
import time;
import json;
import os;



ran_insts = {
    "screenmon": {
        "proc":   None,
        "active": False
    },
    
    "procmon": {
        "proc":   None,
        "active": False
    }, 
    
    "sleepmon": {
        "proc":   None,
        "active": False
    }
};

# stdin

def send_payload(proc, payload: bytes):
    proc.stdin.write(payload);
    proc.stdin.flush();
    proc.stdin.close();

# helpers

def is_proc_alive(proc):    
    return (proc is not None) and (proc.poll() is None);

def kill_proc(proc):
    if (is_proc_alive(proc)):
        proc.kill();
        proc.wait();

def after_run(proc_field, proc):
    ran_insts[proc_field]["proc"]   = proc;
    ran_insts[proc_field]["active"] = is_proc_alive(proc);

# alive ...

def is_procmon_alive():
    return is_proc_alive(ran_insts["procmon"]["proc"]);

def is_screenmon_alive():
    return is_proc_alive(ran_insts["screenmon"]["proc"]);

def is_sleepmon_alive():
    return is_proc_alive(ran_insts["sleepmon"]["proc"]);

# kill ...

def kill_procmon():
    procmon = ran_insts["procmon"];
    
    kill_proc(procmon["proc"]);
    procmon["active"] = False;

def kill_screenmon():
    screenmon = ran_insts["screenmon"];

    kill_proc(screenmon["proc"]);
    screenmon["active"] = False;

def kill_sleepmon():
    sleepmon = ran_insts["sleepmon"];
    
    kill_proc(sleepmon["proc"]);
    sleepmon["active"] = False;


def _run_procmon(allowed_procs: list[str]):
    payload = json.dumps(allowed_procs);
    payload = payload.encode("utf-8");
    
    procmon = subprocess.Popen(
        [MON_EXE_PATH, "--procmon"],
        stdin=subprocess.PIPE,
        text=False
    );
    
    send_payload(procmon, payload);
    
    after_run("procmon", procmon);


# main runners

def run_procmon_no_check(allowed_procs: list[str]):
    _run_procmon(allowed_procs);

def run_procmon(allowed_procs: list[str]):
    if (DISABLE_WHITELIST_ENFORCER):
        return;
    
    if is_procmon_alive():
        kill_procmon();
    
    _run_procmon(allowed_procs);

def run_screenmon():
    if (is_screenmon_alive()):
        kill_screenmon();
    
    screenmon = subprocess.Popen(
        [MON_EXE_PATH, "--screenmon"]
    );
    
    after_run("screenmon", screenmon);

def run_sleepmon(sleep_times: list[str]):
    if (is_sleepmon_alive()):
        kill_sleepmon();
    
    payload = json.dumps(sleep_times);
    payload = payload.encode("utf-8");
    
    sleepmon = subprocess.Popen(
        [MON_EXE_PATH, "--sleepmon"],
        stdin=subprocess.PIPE,
        text=False
    );
    
    send_payload(sleepmon, payload);
    
    after_run("sleepmon", sleepmon);


SLEEP_INTERVAL = 0.1;

def emergency_exit():
    for mon in ran_insts:
        kill_proc(mon["proc"]);
    os._exit(1);

def watch_procs_thread():
    while True:
        for mon in ran_insts:
            # mon["proc"] == True and mon["active"] == True
            # means that the process is ran by stoic.exe and that it exists
            
            # mon["proc"] == False and mon["active"] == False
            # means that the process was not killed (crashed) by stoic.exe
            # since active-flag is set to True
            
            if ((is_proc_alive(mon["proc"]) is False) and (mon["active"] is True)):
                # service.exe will restart stoic.exe since emergency exit terminates all threads and procs
                emergency_exit();
            
            time.sleep(SLEEP_INTERVAL);

def start_watch_procs_thread():
    thread = threading.Thread(
        target=watch_procs_thread,
        daemon=True
    );
    
    thread.start();

