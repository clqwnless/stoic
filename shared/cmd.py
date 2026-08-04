from .time_utils import str_to_unix;

import os;


RESET   = "\033[0m"

BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

BRIGHT_BLACK   = "\033[90m"
BRIGHT_RED     = "\033[91m"
BRIGHT_GREEN   = "\033[92m"
BRIGHT_YELLOW  = "\033[93m"
BRIGHT_BLUE    = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN    = "\033[96m"
BRIGHT_WHITE   = "\033[97m"

# request (cmd)


# term api 

def cls():
    os.system("cls");

def pause():
    os.system("pause");

def request_device():
    from .eth        import get_devices; # lazy import
    # using lazy import because the absolute import breaks cold_start.py if config.json is not created

    devices = get_devices();
    
    while True:
        # rendering devices
        
        cls();
        
        print();
        for index, device in enumerate(devices):
            print(f" - {BRIGHT_RED}[{index}]{RESET} {BRIGHT_GREEN}[{device}]{RESET}");
        
        
        choice = input("\n>>> ");

        if (choice == "x"):
            return None;
        
        choice = int(choice);

        if (choice is not None and 0 <= choice < len(devices)):
            return devices[choice];

def request_date_filter():
    inp = None;
    
    while True:
        cls();
        
        print(f"\ndate_filter (not required), {BRIGHT_GREEN}format=%Y-%m-%d{RESET} ; example: {BRIGHT_GREEN}2026-07-15{RESET}");
        print("type \"x\" to exit\n");
        
        print(f"current date_filter={inp}");
        
        next_inp = input(f"\n{BRIGHT_RED}date_filter: {RESET}")

        if (next_inp == "x"):
            break;
        
        inp = next_inp;
    
    try:
        date_filter = str_to_unix(inp, "%Y-%m-%d");
    except Exception as e:
        print(f"\n{BRIGHT_RED}err:{RESET} {e}\n");
        print(f"{BRIGHT_GREEN}ignoring error: ...{RESET}");
    
        return None;
    else:
        return date_filter;



