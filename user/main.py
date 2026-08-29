from shared.config import (
    SNAPSHOTS_JSON,
    LOCAL_JSON,
    ROOT_PATH,
    EXTENSIONS_JSON,
    DEVICE_ID,
    IS_COMPILED,
    SLEEP_TIMES,
    DISABLE_WHITELIST_ENFORCER
);


from shared.utils      import read_json, write_json, get_block_pairs, disable_ctrl_c;

from shared.eth        import get_date_folders, get_results_json, get_bins;

from shared.cmd        import *;
from shared.time_utils import *;

from user.winapi import run_proc_from_current_session, disable_close_button;

# from current directory
from user import watchdog;
from user import updater;

import os;
import time;
import builtins;
import multiprocessing;
import json;
import subprocess;
import sys;
import secrets;
import traceback;


# GLOBAL VARIABLES

snapshots          = None;
local              = None;
extensions         = None;



# render

main_menu = '''
  shutdown ; reboot ; bios ; win_re ; exit

  [1] Plan
  [2] Execute
  [3] Processes Info
  [4] View History
  [5] Progress
  [6] View Blocks
  [7] Extensions
  [8] Update
'''

plan_menu = '''
  add [mode index] (use if whitelist_enforcer is enabled)
  new              (use if whitelist_enforcer is disabled)
  push
'''

execute_menu = '''
  options: finish
'''

progress_menu = '''
  options: date_filter
'''

ext_menu      = '''
  options: run_ext
'''


# built-ins

def input(prompt=""):
    try:
        return builtins.input(prompt);
    except (EOFError, KeyboardInterrupt):
        return;

def int(value) -> int | None:
    try:
        return builtins.int(value)
    except (ValueError, TypeError):
        return None;

# another

def run_proc(allowed_proc: list, proc_index: str):
    proc_index = int(proc_index);
    
    # checking if index is valid 
    
    if proc_index is None:
        return;
    
    if not (0 <= proc_index < len(allowed_proc)):
        return;

    # hidden check
    
    if (proc_index > 0 and allowed_proc[proc_index - 1] == "hidden"):
        return;
    
    if (allowed_proc[proc_index] == "hidden"):
        return;
    
    proc_path = allowed_proc[proc_index];
    
    #if (not os.path.exists(proc_path)):
    #    print(f"\nthe specified file doesn't exist: {proc_path}\n");
    #    pause();
    #    return;
    
    run_proc_from_current_session(proc_path);


def run_extension(ext):
    try:
        subprocess.run([ext["entry_point"]]);
    except:
        pass;

def on_exit():
    if (watchdog.whitelist_enforcer is not None):
        watchdog.whitelist_enforcer.terminate();
    
    if (watchdog.recorder is not None):
        watchdog.recorder.terminate();
    
    if (watchdog.sleep_times_enforcer is not None):
        watchdog.sleep_times_enforcer.terminate();
    
    write_json(LOCAL_JSON, local);

def enter_win_re():
    args = [
        "shutdown",
        "/r",
        "/o",
        "/f",
        "/t",
        "0"
    ];
    subprocess.run(args, shell=True);

def enter_bios():
    args = [
        "shutdown",
        "/r",
        "/fw",
        "/t",
        "0"
    ];
    subprocess.run(args, shell=True);

def reboot():
    args = [
        "shutdown",
        "/r",
        "/f",
        "/t",
        "0"
    ];
    subprocess.run(args, shell=True);

def shutdown():
    args = [
        "shutdown",
        "/s",
        "/t",
        "0"
    ];
    subprocess.run(args, shell=True);


# data

def gen_event(event_type, mode_index=None, task=None, cause=None):
    
    event = {};
    
    event["id"]    = secrets.token_hex(8);
    event["time"]  = get_current_time();

    event["event"] = event_type;
    
    # adding task
    
    if (event_type == "block_started"):
        event["worked_seconds"] = 0;
        event["task"]  = task;
        event["mode_index"] = mode_index;
    
    # adding cause
    
    if (event_type in ["block_finished"]):
        event["cause"] = cause;
    
    return event;

def add_event(event):
    local["events"].append(event);
    #local["seq"] += 1;

def find_active_block(history):
    for event in reversed(history):
        if event["event"] == "block_started":
            return event;
        if event["event"] == "block_finished":
            return None;
    return None;

def get_allowed_proc(active_block):
    if (DISABLE_WHITELIST_ENFORCER):
        return [];
    
    mode_index   = active_block["mode_index"];
    mode         = local["modes"][mode_index];

    allowed_proc = mode["allowed_proc"];
    return allowed_proc;

def get_current_state():
    if not local["events"]:
        return "idle";

    event = local["events"][-1]["event"];

    if event == "block_started":
        return "active";

    if event == "block_finished":
        return "idle";



# page helpers

# plan_page helpers

def plan_next_block(mode_index):
    task = input("task description:\n");

    event = gen_event(event_type="block_started", mode_index=mode_index, task=task, cause=None);
    return event;

# execute_page helpers

    # возвращают по сути True || False по сути cont если cont=False то return иначе продолжается execute_page


def finish_execute():
    cause = input("cause:\n");
    if (cause == "x"):
        return True;
    
    while True:
        are_you_sure = input("are you sure? (y/n): ");
        
        if (are_you_sure in ["x", "n"]):
            return True;
        
        if (are_you_sure == "y"):
            break;
    
    event = gen_event(event_type="block_finished", cause="cause");
    add_event(event);
    
    print("finished task\n");
    pause();
    
    return False;

def active_block_checker():
    active_block = find_active_block(local["events"]);
    if (active_block is None):
        cls();
        print("\nerr: no active block\n");
        pause();
        return False;
    
    return True;


def sleep_control():
    for sleep_time in SLEEP_TIMES:
        current_time = get_local_hour_minute();
        start_time   = tuple(sleep_time[:2]);
        end_time     = tuple(sleep_time[2:]);
        
        if (is_time_in_range(start_time, current_time, end_time)):
            cls();
            print("\nerr: sleep time\n");
            print(f"  start_time   = {start_time[0]}:{start_time[1]}");
            print(f"  current_time = {current_time[0]}:{current_time[1]}");
            print(f"  end_time     = {end_time[0]}:{end_time[1]}\n");
            pause();
            return False;
    
    return True;

def on_exit_execute_page(start_time, active_block):
    worked_seconds = get_worked_seconds(start_time, active_block);
    if (worked_seconds is not None):
        active_block["worked_seconds"] = worked_seconds;

def get_worked_seconds(start_time, active_block):
    res = None;
    
    if (active_block is not None):
        sec_delta = get_current_time() - start_time;
        res       = active_block["worked_seconds"] + sec_delta;
    
    return res;

# ...

def render_allowed_processes(allowed_proc):
    # rendering allowed processes

    for index in range(len(allowed_proc)):
        proc = allowed_proc[index];
        
        # skipping hidden processes
        
        if (proc == "hidden"):
            continue;
        
        if (index > 0 and allowed_proc[index - 1] == "hidden"):
            continue;
        
        proc_name = proc.split('\\')[-1];
        
        print(f"  [{index}] - {proc_name}");

# pages


def plan_page():
    # checking if planning is allowed

    active_block = find_active_block(local["events"]);
    
    if (active_block is not None):
        cls();
        print("\nerr: found an active block:\n");
        print(f"\ttask: {active_block["task"]}\n");
        pause();
        return;

    next_block = None;
    
    while True:
        cls();
        
        print(plan_menu);
        
        # render modes
        
        print("modes:\n");
        for index, mode in enumerate(local["modes"]):
            print(f"  [{index}] - {mode["name"]}");
        
        # rendering next_block
        
        print(f"\nnext_block: {next_block}\n");

        # input
        
        opt = input(">>> ");
        
        if (opt == "x"):  return;
        if (opt is None): continue;
        
        if (opt[:4] == "add " and not DISABLE_WHITELIST_ENFORCER):
            index = int(opt[4:]);
            if (index is None): continue;
            
            next_block = plan_next_block(index);
        elif (opt == "new" and DISABLE_WHITELIST_ENFORCER):
            next_block = plan_next_block(None);
        elif (opt == "push"):
            add_event(next_block);
            
            print("ok\n")
            pause();


def execute_page():
    # checling if there is an active schedule now
    

    start_time   = get_current_time();
    active_block = find_active_block(local["events"]);

    if (not active_block_checker()): return;

    allowed_proc = get_allowed_proc(active_block);
    
    # enabling watchdog
    
    watchdog.wd_whitelist_enforcer(allowed_proc=allowed_proc);
    
    while True:
        if (not sleep_control()):
            return;
        
        # rendering
        
        cls();
        
        # rendering menu
        
        print(execute_menu);
        
        # rendering current schedule metadata
        
        print(f"active_task: {active_block["task"]}\n");
        
        # rendering current worked hours and minutes
        
        worked_seconds               = get_worked_seconds(start_time, active_block);
        worked_hours, worked_minutes = sec_to_hour_min(worked_seconds);
        
        print(f"{BRIGHT_GREEN}worked_hours={worked_hours}, worked_minutes={worked_minutes}{RESET}\n");
        
        render_allowed_processes(allowed_proc);

        # getting input

        opt = input("\n>>> ");
        if (opt == "x"):
            on_exit_execute_page(start_time, active_block);
            return;

        if (opt == "finish" and not finish_execute()):
            on_exit_execute_page(start_time, active_block);
            return;
        
        run_proc(allowed_proc, opt);

def processes_info_page():
    cls();
    print("\nProcesses:\n");
    
    # bro, whitelist_enforcer will always be False if it was runned by sleep_times_enforcer 
    # since I don't want to implement shared space between sleep_times_enforcer and current process (main) now
    # and "exit" in main won't work if whitelist_enforcer was runned by sleep_times_enforcer since it is still running
    
    print(f" - whitelist_enforcer:   alive={watchdog.whitelist_enforcer.is_alive() if watchdog.whitelist_enforcer else False}");
    print(f" - sleep_times_enforcer: alive={watchdog.sleep_times_enforcer.is_alive() if watchdog.sleep_times_enforcer else False}");
    print(f" - recorder:             alive={watchdog.recorder.is_alive() if watchdog.recorder else False}\n");
    

    pause();

def view_history_page():
    cls();
    print();
    
    for event in local["events"]:
        time_str = unix_to_localstr(event["time"]);
        
        cause = f"cause={event["cause"]} " if "cause" in event else "";
        task  = f"task={event["task"]} "   if "task"  in event else "";
        
        #event_render = event["event"];
        
        event_type = event["event"];
        
        if (event_type   == "block_started"):
            event_render = f"{BRIGHT_RED}{event_type}{RESET}";
        elif (event_type == "block_finished"):
            event_render = f"{BRIGHT_MAGENTA}{event_type}{RESET}";
        
        print(f" - {BRIGHT_GREEN}[{time_str}]{RESET} {event_render} {BRIGHT_YELLOW}{cause}{RESET}{BRIGHT_WHITE}{task}{RESET}");
    
    print();
    pause();

def results_viewer(folder_name):
    results  = get_results_json(DEVICE_ID, folder_name);
    binaries = get_bins(DEVICE_ID, folder_name);

    while True:
        cls();
        
        
        # rendering results
        
        
        
        print();
        for file_name in binaries:
            
            # там просто может results вернутся {} ; а в случае binaries там может вернуться [] при ошибке
            if (bool(results) and file_name in results["files"]):
                file     = results["files"][file_name];
                
                status   = file["status"];
                comment  = file["comment"];
            else:
                status   = "UNDEFINED";
                comment  = "none";
            
            # где пробелы там по сути выравнивание получается (alignment using spaces) 
            
            if (status == "OK"):
                status_renderable = f"{BRIGHT_GREEN}OK{RESET}";
                status_renderable += (' ' * 7);
            elif (status == "NOT OK"):
                status_renderable = f"{BRIGHT_RED}NOT OK{RESET}";
                status_renderable += (' ' * 3);
            elif (status == "UNDEFINED"):
                status_renderable = status;
            
            
            # заменяем все \n на пробелы
            comment = comment.replace("\n", "");
            
            if (bool(comment) and comment[-1] == '\n'):
                comment = comment[:-1]
            
            
            print(f" - [{status_renderable}] [{BRIGHT_YELLOW}{file_name}{RESET}] [{comment}]");

        inp = input("\n>>> ");
        
        if (inp == "x"):
            return;

def progress_viewer():
    date_filter = None;
    
    date_folders = get_date_folders(DEVICE_ID, date_filter);
    
    while True:
        cls();
        
        print(progress_menu);
        
        print(f"  date_filter={date_filter}\n")
        
        # rendering device folders
        
        if (date_folders is not None):
            for index, folder in enumerate(date_folders):
                print(f" - {BRIGHT_RED}[{index}]{RESET} {BRIGHT_GREEN}{folder}{RESET}");
        
        inp = input("\n>>> ");
        if (inp == "x"):
            return;        
        elif (inp == "date_filter"):
            date_filter = request_date_filter();
            
            # updating date_folders
            if (date_filter is not None):
                date_folders = get_date_folders(date_filter);
        else:
            
            folder_index = int(inp);
            if (folder_index is not None and 0 <= folder_index < len(date_folders)):
                folder_name = date_folders[folder_index];
                results_viewer(folder_name);

def view_blocks():
    block_pairs = get_block_pairs(local);
    
    cls();
    print();
    
    for pair in block_pairs:
        block_started  = pair[0];
        start_time     = unix_to_localstr(block_started["time"]);
        
        
        
        # getting block_duration_seconds and end_time
        if (len(pair) == 2):
            block_finished = pair[1];
            
            end_time       = unix_to_localstr(block_finished["time"]);
            block_duration_seconds = block_finished["time"] - block_started["time"];
        else:
            block_duration_seconds = get_current_time() - block_started["time"];
            end_time = "current";
        
        # getting block duration
        
        block_duration_hours, block_duration_minutes = sec_to_hour_min(block_duration_seconds);
        
        # getting worked hours and minutes
        
        worked_hours, worked_minutes = sec_to_hour_min(block_started["worked_seconds"]);

        
        
        r1 = f"{BRIGHT_RED}{block_started["task"]}{RESET}";
        
        r2 = f"{BRIGHT_GREEN}{start_time}{RESET}";
        r3 = f"{BRIGHT_YELLOW}{end_time}{RESET}";
        r4 = f"{BRIGHT_MAGENTA}duration:{RESET} {BRIGHT_CYAN}hours={block_duration_hours}, minutes={block_duration_minutes}{RESET}";
        
        r5 = f"worked:   hours={worked_hours}, minutes={worked_minutes}";
        
        print(f"\n - [{r1}]");
        print(f"   - {r2} - {r3}");
        print(f"   - {r4}");
        print(f"   - {r5}");
        
        #print(f" - [{r1}] [{r2}] [{r3}] [{r4}] [{r5}]");
       # print(f"   - [{r4}]");
        
    
    print();
    pause();

def ext_page(ext):
    watchdog.wd_whitelist_enforcer(allowed_proc=ext["user_allowed_proc"]);

    while True:
        # rendering

        cls();
        
        print(ext_menu);
        print(f"ext: {ext["name"]}\n");
        
        render_allowed_processes(ext["user_allowed_proc"]);

        inp = input("\n>>> ");
        
        if (inp == "x"):
            return;
        elif (inp == "run_ext"):
            run_extension(ext);
        else:
            run_proc(ext["user_allowed_proc"], inp);



def extensions_page():
    if (extensions is None):
        cls();
        print("\nerr: extensions file not found\n");
        pause();
        return;
    
    while True:
        # rendering
        
        cls();
        
        # rendering extensions
    
        print()
        for index, ext in enumerate(extensions):
            print(f"  [{index}] {ext["name"]}");
        
        inp = input("\n>>> ");
        if (inp == "x"):
            return;
        
        index = int(inp);
        
        if (index is not None and 0 <= index < len(extensions)):
            ext_page(extensions[index]);
            watchdog.wd_whitelist_enforcer(allowed_proc=[]);


# main

def main():
    watchdog.wd_whitelist_enforcer(allowed_proc=[]);
    watchdog.wd_recorder();
    
    if (bool(SLEEP_TIMES)):
        watchdog.wd_sleep_times_enforcer(SLEEP_TIMES);
    
    while True:
        cls();
        
        #print(os.getpid());
        
        print(main_menu);
        
        opt = input(">>> ");
        
        if (opt == "exit"):
            on_exit();
            exit(0);
        elif (opt == "shutdown"):
            on_exit();
            shutdown();
        elif (opt == "win_re"):
            on_exit();
            enter_win_re();
        elif (opt == "bios"):
            on_exit();
            enter_bios();
        elif (opt == "reboot"):
            on_exit();
            reboot();
        elif (opt == "1"):
            plan_page();
        elif (opt == "2"):
            execute_page();
            
            # after exit from executer
            
            watchdog.wd_whitelist_enforcer(allowed_proc=[]);
        elif (opt == "3"):
            processes_info_page();
        elif (opt == "4"):
            view_history_page();
        elif (opt == "5"):
            progress_viewer();
        elif (opt == "6"):
            view_blocks();
        elif (opt == "7"):
            extensions_page();
        elif (opt == "8"):
            updater.start();





if __name__ == "__main__":
    snapshots = read_json(SNAPSHOTS_JSON);
    local     = read_json(LOCAL_JSON);
    
    if (os.path.exists(EXTENSIONS_JSON)):
        extensions = read_json(EXTENSIONS_JSON);

    disable_close_button();
    disable_ctrl_c();

    os.chdir(ROOT_PATH);
    
    
    # restart main func on errors (using pause func so that the user can read the exception)
    
    while True:
        try:
            main();
        except Exception as e:
            print(f"main err: {e}");
            traceback.print_exc();
            print();
            pause();
