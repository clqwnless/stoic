from pathlib import Path;
from shared.utils import read_json;

import os;
import sys;
import __main__;




USER_JSON_COLD_START = {
    "device_id": "stoic user",
    
    "disable_whitelist_enforcer": True,

    "system_proc_pairs": [
        ["System", ""],
        ["Registry", "Registry"],
        ["smss.exe", "C:\\Windows\\System32\\smss.exe"],
        ["lsass.exe", "C:\\Windows\\System32\\lsass.exe"],
        ["csrss.exe", "C:\\Windows\\System32\\csrss.exe"],
        ["wininit.exe", "C:\\Windows\\System32\\wininit.exe"],
        ["services.exe", "C:\\Windows\\System32\\services.exe"],
        ["winlogon.exe", "C:\\Windows\\System32\\winlogon.exe"],
        ["svchost.exe", "C:\\Windows\\System32\\svchost.exe"],
        ["fontdrvhost.exe", "C:\\Windows\\System32\\fontdrvhost.exe"],
        ["dwm.exe", "C:\\Windows\\System32\\dwm.exe"],
        ["explorer.exe", "C:\\Windows\\explorer.exe"],
        ["sihost.exe", "C:\\Windows\\System32\\sihost.exe"],
        ["dllhost.exe", "C:\\Windows\\System32\\dllhost.exe"],
        ["taskhostw.exe", "C:\\Windows\\System32\\taskhostw.exe"],
        ["SearchIndexer.exe", "C:\\Windows\\System32\\SearchIndexer.exe"],
        ["RuntimeBroker.exe", "C:\\Windows\\System32\\RuntimeBroker.exe"],
        ["SearchApp.exe", "C:\\Windows\\SystemApps\\Microsoft.Windows.Search_cw5n1h2txyewy\\SearchApp.exe"],
        ["sppsvc.exe", "C:\\Windows\\System32\\sppsvc.exe"],
        ["WmiPrvSE.exe", "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe"],
        ["conhost.exe", "C:\\Windows\\System32\\conhost.exe"],
        ["LogonUI.exe", "C:\\Windows\\System32\\LogonUI.exe"],
        ["StartMenuExperienceHost.exe", "C:\\Windows\\SystemApps\\Microsoft.Windows.StartMenuExperienceHost_cw5n1h2txyewy\\StartMenuExperienceHost.exe"],
        ["audiodg.exe", "C:\\Windows\\System32\\audiodg.exe"],
        ["ctfmon.exe", "C:\\Windows\\System32\\ctfmon.exe"],
        ["service.exe", "C:\\Users\\admin\\Desktop\\service\\service.exe"]
    ],
    
    "screenshot_delay_interval": 30,
    "sleep_times": []
}



def PATH(*args):
    return os.path.join(*args);

# called in this file and user_service.main

# getting root path

IS_COMPILED = hasattr(__main__, "__compiled__");

if (IS_COMPILED):
    # main.exe -> parent
    ROOT_PATH = Path(sys.argv[0]).resolve().parent;
else:
    # config.py -> shared -> stoic
    ROOT_PATH = Path(__file__).resolve().parent.parent;


# folders

DB_PATH           = PATH(ROOT_PATH, "db");
SCREENSHOTS_PATH  = PATH(DB_PATH, "screenshots");
UPDATES_CACHE_DIR = PATH(ROOT_PATH, "temp", "updates_cache");

# ...

PENDING_UPDATE_FILE = PATH(ROOT_PATH, "temp", "pending_update.json");

UPDATE_FILE_NAME    = "stoic_update.json";
UPDATE_FILE         = PATH(ROOT_PATH, UPDATE_FILE_NAME);

# json paths

USER_JSON        = PATH(DB_PATH, "user.json");
SNAPSHOTS_JSON   = PATH(DB_PATH, "snapshots.json");
LOCAL_JSON       = PATH(DB_PATH, "local.json");
CONFIG_JSON      = PATH(DB_PATH, "config.json"); # also used in verifier
PUBLIC_KEY_PATH  = PATH(DB_PATH, "public_key.pem");
PRIVATE_KEY_PATH = PATH(DB_PATH, "private_key.pem"); # only for verifier
EXTENSIONS_JSON  = PATH(DB_PATH, "extensions.json"); # isn't necessary

# getting user data

if (os.path.exists(USER_JSON)):
    USER_DATA = read_json(USER_JSON);
else:
    USER_DATA = USER_JSON_COLD_START;


# if the setting below is set to true, the stoic won't kill processes that doesn't match the whitelist
# basically, then the whitelist is disabled, there are no problems with running other processes that are not in this list
# otherwise, if you want to torque yourself (as i realized later), set it to False

DISABLE_WHITELIST_ENFORCER = USER_DATA["disable_whitelist_enforcer"];

# desktop info

DEVICE_ID     = USER_DATA["device_id"];

# system proc

SYSTEM_PROC_PAIRS = USER_DATA["system_proc_pairs"];

# screenshot delay

SCREENSHOT_DELAY_INTERVAL = USER_DATA["screenshot_delay_interval"];

# sleep times

SLEEP_TIMES   = USER_DATA["sleep_times"];
