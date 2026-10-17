from shared.time_utils import get_current_time, get_current_time_str, is_time_in_range, get_local_hour_minute;
from user.mon_runner   import run_procmon_no_check, kill_procmon;


SLEEP_INTERVAL = 1;


def get_time_range(st: str):
    # format HH:MM-HH:MM
    
    start, end = st.split("-")

    start = tuple(map(int, start.split(":")))
    end = tuple(map(int, end.split(":")))

    return start, end

def sleepmon(sleep_times: list):
    while True:
        for st in sleep_times:
            start_time, end_time = get_time_range(st);
            current_time         = get_local_hour_minute();
            
            if (is_time_in_range(start_time, current_time, end_time)):
                run_procmon_no_check([])
            elif (whitelist_enforcer is not None):
                kill_procmon();
            
            time.sleep(SLEEP_INTERVAL);


