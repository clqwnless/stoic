import json;
import signal;
import functools;
import traceback;
import time;

# json api

def read_json(file_path):
    with open(file_path, "r") as file:
        data = json.load(file);
    return data;

def write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4);

# block pairs

def get_block_pairs(status):
    pairs = [];
    
    current_pair_index = 0;
    
    for e in status["events"]:
        event_type = e["event"];
        
        if (event_type == "block_started"):
            pairs.append([]); # creating new list
            pairs[-1].append(e);
        elif (event_type == "block_finished"):
            pairs[-1].append(e);

    return pairs;

def find_task_by_timestamp(status, timestamp):
    # label basically
    
    block_pairs = get_block_pairs();
    
    for pair in block_pairs:
        if (len(pair) == 2):
            block_started  = pair[0];
            block_finished = pair[1];
        elif (len(pair) == 1):
            block_started = pair[0];
            block_finished = None;
        
        if (block_finished is None and block_started["time"] <= timestamp):
            return block_started;

        if (block_finished is not None and block_started["time"] <= timestamp <= block_finished["time"]):
            return block_started;
    
    return None; 

# ...

def disable_ctrl_c():
    signal.signal(signal.SIGINT, signal.SIG_IGN);


def restart_func_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs);
            except Exception as e:
                print(f"err: func name: {func.__name__}: {e}");
                traceback.print_exc();
    
    return wrapper;

