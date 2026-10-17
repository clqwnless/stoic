from shared.config import MON_EXE_PATH;
import subprocess;
import json;


ran_insts = {
    "screenmon": None,
    "procmon":   None,
    "sleepmon":  None
};


def send_payload(proc, payload: bytes):
    proc.stdin.write(payload);
    proc.stdin.flush();
    proc.stdin.close();


def run_screenmon():
    screenmon = subprocess.Popen(
        [MON_EXE_PATH, "--screenmon"]
    );
    
    ran_insts["screenmon"] = screenmon;

def run_procmon(allowed_procs: list[str]):
    payload = json.dumps(allowed_procs);
    payload = payload.encode("utf-8");
    
    procmon = subprocess.Popen(
        [MON_EXE_PATH, "--procmon"],
        stdin=subprocess.PIPE,
        text=False
    );
    
    send_payload(procmon, payload);
    
    ran_insts["procmon"] = procmon;

def run_sleepmon(sleep_times: list[str]):
    payload = json.dumps(sleep_times);
    payload = payload.encode("utf-8");
    
    sleepmon = subprocess.Popen(
        [MON_EXE_PATH, "--sleepmon"],
        stdin=subprocess.PIPE,
        text=False
    );
    
    send_payload(sleepmon, payload);
    
    ran_insts["sleepmon"] = sleepmon;
    



