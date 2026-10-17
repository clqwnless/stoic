from user.mon.screenmon import screenmon;
from user.mon.procmon   import procmon;
from user.mon.sleepmon  import sleepmon;


import sys;
import json;


def get_payload():
    data = sys.stdin.buffer.read();
    data = data.decode("utf-8");
    payload = json.loads(data);
    
    return payload;

def show_help():
    print();
    print("stoic monitor\n")
    print("args:\n");
    print("\t--screenmon");
    print("\t--procmon  (requires payload)");
    print("\t--sleepmon (requires payload)");
    print();
    print("payload data are passed in stdin ; for more info check mon_runner.py");
    print("mon_runner.py implements an entry point so that you can run this file")

if __name__ == "__main__":
    args = sys.argv;
    
    if (len(args) <= 1):
        show_help();
        exit(-1);
    
    mon = args[1];
    
    if (mon == "--screenmon"):
        screenmon();
    elif (mon == "--procmon"):
        print("getting json in stdin ; awaiting json (list) with allowed procs");
        procmon(get_payload()); 
    elif (mon == "--sleepmon"):
        print("getting json in stdin ; awaiting json (list) with sleep times");
        print("the expected format of strings is: HH:MM-HH:MM, example: 10:00-17:30");
        sleepmon(get_payload());
    
    


