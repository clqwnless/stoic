from shared.config import (
    SCREENSHOTS_PATH,
    USER_JSON,
    SNAPSHOTS_JSON,
    LOCAL_JSON,
    CONFIG_JSON,
    PUBLIC_KEY_PATH,
    PRIVATE_KEY_PATH
);

from shared.cmd    import *;
from shared.utils  import write_json;

import os;


SNAPSHOTS_JSON_COLD_START = [];

LOCAL_JSON_COLD_START     = {
    "modes": [
        {
            "name": "cmd",
            "allowed_proc": [
                "C:\\Windows\\system32\\cmd.exe"
            ]
        }
    ],
    
    "events": []
};

CONFIG_JSON_COLD_START    = {
    "refresh_token": "insert your refresh token (dropbox) ; you can get the refresh by using get_refresh_token.py",
    "app_key":       "insert your app key (dropbox)",
    "app_secret":    "insert your app secret (dropbox)",
};

USER_JSON_COLD_START      = {
    "db_path": "",
    "device_id": "",

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


def FILE_EXISTS(path: str):
    return os.path.exists(path);

print("\nChecking the existence of db files\n");
print(f"  SCREENSHOTS_PATH  = {FILE_EXISTS(SCREENSHOTS_PATH)}");
print(f"  USER_JSON         = {FILE_EXISTS(USER_JSON)}");
print(f"  SNAPSHOTS_JSON    = {FILE_EXISTS(SNAPSHOTS_JSON)}");
print(f"  LOCAL_JSON        = {FILE_EXISTS(LOCAL_JSON)}");
print(f"  CONFIG_JSON       = {FILE_EXISTS(CONFIG_JSON)}");
print(f"  PRIVATE_KEY_PATH  = {FILE_EXISTS(PRIVATE_KEY_PATH)}");
print(f"  PUBLIC_KEY_PATH   = {FILE_EXISTS(PUBLIC_KEY_PATH)}\n");



# SCREENSHOTS_PATH

if not FILE_EXISTS(SCREENSHOTS_PATH):
    print(f"{BRIGHT_GREEN}  1. Creating screenshots directory: {SCREENSHOTS_PATH}{RESET}\n");
    os.makedirs(SCREENSHOTS_PATH, exist_ok=True)

# USER_JSON

if not FILE_EXISTS(USER_JSON):
    print(f"{BRIGHT_GREEN}  2. Creating USER_JSON{RESET}\n");
    write_json(USER_JSON, USER_JSON_COLD_START);

# SNAPSHOTS_JSON

if not FILE_EXISTS(SNAPSHOTS_JSON):
    print(f"{BRIGHT_GREEN}  3. Creating SNAPSHOTS_JSON{RESET}\n");
    write_json(SNAPSHOTS_JSON, SNAPSHOTS_JSON_COLD_START);

# LOCAL_JSON

if not FILE_EXISTS(LOCAL_JSON):
    print(f"{BRIGHT_GREEN}  4. Creating LOCAL_JSON{RESET}\n");
    write_json(LOCAL_JSON, LOCAL_JSON_COLD_START);

# CONFIG_JSON

if not FILE_EXISTS(CONFIG_JSON):
    print(f"{BRIGHT_GREEN}  5. Creating CONFIG_JSON:{RESET}\n");
    print(f"{BRIGHT_YELLOW}  6. Insert dropbox data in config.json (consider using get_refresh_token.py){RESET}\n");
    write_json(CONFIG_JSON, CONFIG_JSON_COLD_START);

if not FILE_EXISTS(PUBLIC_KEY_PATH):
    print(f"{BRIGHT_YELLOW}  7. Get the public key from the verifier and copy it to the database folder if you are the user{RESET}\n");
    print(f"{BRIGHT_YELLOW}  Otherwise you can ignore this warning:{RESET}\n");

if not FILE_EXISTS(PRIVATE_KEY_PATH):
    print(f"{BRIGHT_YELLOW}  8. Get the private key if you are the verifier{RESET}\n");
    print(f"{BRIGHT_YELLOW}  Otherwise you can ignore this warning:{RESET}\n");

print(f"{BRIGHT_CYAN}DONE{RESET}\n");

pause();

