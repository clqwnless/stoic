from pathlib import Path;
from shared.utils import read_json;

import os;
import sys;
import __main__;



def PATH(*args):
    return os.path.join(*args);



# data which should be initialized by user in this file

USER_JSON         = r"C:\stoic_db\user.json"
SCREENSHOTS_PATH  = r"C:\stoic_db\screenshots";
UPDATES_CACHE_DIR = r"C:\stoic_updates_cache";

# getting root path

IS_COMPILED = hasattr(__main__, "__compiled__");

if (IS_COMPILED):
    # main.exe -> parent
    ROOT_PATH = Path(sys.argv[0]).resolve().parent;
else:
    # config.py -> shared -> stoic
    ROOT_PATH = Path(__file__).resolve().parent.parent;

# getting user data

USER_DATA = read_json(USER_JSON);

# getting db path

DB_PATH   = USER_DATA["db_path"];

# json paths

SNAPSHOTS_JSON   = PATH(DB_PATH, "snapshots.json");
LOCAL_JSON       = PATH(DB_PATH, "local.json");
CONFIG_JSON      = PATH(DB_PATH, "config.json"); # also used in verifier
PUBLIC_KEY_PATH  = PATH(DB_PATH, "public_key.pem");
PRIVATE_KEY_PATH = PATH(DB_PATH, "private_key.pem"); # only for verifier
EXTENSIONS_JSON  = PATH(DB_PATH, "extensions.json"); # isn't necessary

# exes / scripts paths

GUARDIAN_PATH    = PATH(ROOT_PATH, "user", "guardian.py");
PYTHONW_PATH     = str(Path(sys.executable).with_name("pythonw.exe"));

# desktop info

DEVICE_ID     = USER_DATA["device_id"];

# system proc

SYSTEM_PROC_PAIRS = USER_DATA["system_proc_pairs"];

# screenshot delay

SCREENSHOT_DELAY_INTERVAL = USER_DATA["screenshot_delay_interval"];

# sleep times

SLEEP_TIMES   = USER_DATA["sleep_times"];

