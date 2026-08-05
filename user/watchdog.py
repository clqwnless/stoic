from PIL               import ImageGrab;

from shared.config     import SCREENSHOTS_PATH, SCREENSHOT_DELAY_INTERVAL, SYSTEM_PROC_PAIRS, SNAPSHOTS_JSON;
from shared.time_utils import get_current_time, get_current_time_str;

from shared.utils      import read_json, write_json, disable_ctrl_c, restart_func_on_error;

from shared.eth        import push_snapshots, upload_local;
from shared.acl        import apply_basic_rule;



import psutil;
import os;
import random;
import time;
import signal;


# for debug basically

DEBUG   = True;
USE_ETH = True;


snapshots = read_json(SNAPSHOTS_JSON);
#print(snapshots);


# snapshot (json)
# hidden api

def make_screenshot(path):
    # saving screenshot
    
    screenshot = ImageGrab.grab();
    screenshot.save(path);
    
    # permission rights
    
    apply_basic_rule(path, log=False);
    

def new_snapshot_obj():
    utc             = get_current_time();
    screenshot_name = str(utc) + '.jpg';
    path            = os.path.join(SCREENSHOTS_PATH, screenshot_name);
    
    obj = {
        "screenshot_path": path,
        "utc": utc,
        "sent": False
    };
    
    return obj;

# public api

def get_snapshot_delay():
    if (DEBUG):
        delay = random.randint(0, 60);
        rest  = 0;
    else:
        total_sec = SCREENSHOT_DELAY_INTERVAL * 60;
        
        delay = random.randint(0, total_sec);
        rest  = total_sec - delay;
    return delay, rest;

def do_snapshot():
    obj = new_snapshot_obj();
    make_screenshot(obj["screenshot_path"]);
    return obj;

# other

def get_allproc():
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


# watchdogs

@restart_func_on_error
def wd_record():
    disable_ctrl_c();

    while True:
        delay, rest = get_snapshot_delay();
        time.sleep(delay);
        
        s = do_snapshot();
        snapshots.append(s);
        
        write_json(SNAPSHOTS_JSON, snapshots);
        
        # eth part
        
        if (USE_ETH):
            push_snapshots(snapshots);
            upload_local();
            
        
        time.sleep(rest);
        
        # если даже далее sent = False (а может и такое быть - то оно re-upload сделает просто короче позже)
        # write_json(SNAPSHOTS_JSON, snapshots);
        # можно это написать мол после sent чтобы было еще - но хз
        
        # updating snapshots file (json) (making a backup)

@restart_func_on_error
def wd_enforce_whitelist(allowed_proc: list):
    disable_ctrl_c();
    
    sleep_interval = 0.1; # not to overload the processor
    current_time   = get_current_time(); 
    
    
    # делаем одним регистром (по сути приводим к общему знаменателю иначе proc in allowed_proc может не работать)
    allowed_proc = [proc.lower() for proc in allowed_proc];
    
    while True:
        # если unix_until is None то там ожидается что main убьёт этот процесс сам короче (мы юзаем модуль multiprocessing)
        
        runned_processes = get_allproc();

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
            
            # (runned as not admin) & (is not system proc) & (is not allowed_proc)
            
            #kill_proc(pid);
        
        current_time = get_current_time();
        time.sleep(sleep_interval);



# helper function

def find_system_proc_pairs(dest_path):
    import secrets;


    SYSTEM_PROC_NAMES = [
        "WMIC.exe",
        "WmiPrvSE.exe",
        "RuntimeBroker.exe",
        "System",
        "fontdrvhost.exe",
        "lsass.exe",
        "services.exe",
        "taskhostw.exe",
        "System Idle Process",
        "NVDisplay.Container.exe",
        "dasHost.exe",
        "audiodg.exe",
        "smss.exe",
        "SearchIndexer.exe",
        "WindowsInternal.ComposableShell.Experiences.TextInput.InputApp.exe",
        "winlogon.exe",
        "dllhost.exe",
        "conhost.exe",
        "csrss.exe",
        "ShellExperienceHost.exe",
        "sihost.exe",
        "explorer.exe",
        "spoolsv.exe",
        "SearchApp.exe",
        "svchost.exe",
        "sppsvc.exe",
        "Registry",
        "dwm.exe",
        "wininit.exe",
        "ctfmon.exe"
    ]

    processes = get_allproc();
    
    exes = {};
    
    for proc_name, proc_exe, _, _ in processes:
        if (proc_name in SYSTEM_PROC_NAMES):
            p = (proc_name, proc_exe);
            
            if (proc_name in exes):
                if (proc_exe != exes[proc_name]):
                    token = secrets.token_hex(4);
                    exes[proc_name + ' ' + token] = proc_exe;
                
                # иначе игнорируем (поскольку идентичны)
                continue;
            
            exes[proc_name] = proc_exe;
    
    
    file_content = '';
    file_content += '"system_proc_pairs": [\n';
    
    for proc_name, proc_exe in exes.items():
        
        current_string = f'["{proc_name}", "{proc_exe}"]';
        
        # replacing one '\' with two '\\' so that json is readable (so that there are no errors during the parsing)
        current_string = current_string.replace("\\", "\\\\");
        
        
        current_string = (' ' * 4) + current_string;
        
        current_string += ',';
        
        file_content += current_string;
        file_content += '\n';

    file_content += ']\n';
    
    with open(dest_path, mode="w") as f:
        f.write(file_content);




if __name__ == "__main__":
    #processes_paths = [r"C:\Windows\explorer.exe"];
    #kill_proc_after(get_current_time()+1, processes_paths);

    #unix_until = 2000000000;
    #allowed_proc = [];
    

    #watchdog_notallowed_prockiller(unix_until, allowed_proc, 7860)
    
    #wd_enforce_whitelist(2000000000, [], None);
    
    #allowed_proc = ["hidden", "some", "cmd.exe"]
    #wd_kill_proc_after(get_current_time() + 1, allowed_proc);


    print(get_allproc());


    find_system_proc_pairs("res.txt");

    #print(exes);
    
    #get_allproc();
    
    
    '''
    from eth import upload_snapshot, upload_local;
    
    s = do_snapshot();
    upload_snapshot(s);
    upload_local();
    -=
    
    #upload_snapshot(s);
    '''
    
    
    
    
    
    
    '''
    from eth import upload_snapshot;
    obj = do_snapshot();
    upload_snapshot(obj);
    '''
    
    ...
    
    #snapshot_maker();
    





