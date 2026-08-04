import os;
import time;
import sys;

from .watchdog import get_allproc;



def run_guardian(main_pid, sleep_interval=0.05):
    while True:
        found = False;
        procs = get_allproc();
        
        for _, _, pid, _ in procs:
            if (pid == main_pid):
                found = True;
        
        if (not found):
            #with open(r"C:\debug.txt", mode="w") as file:
            #    file.write(str(time.time()));
            
            #time.sleep(10);
            
            os.system("shutdown /s /f /t 0");
            return;
        
        time.sleep(sleep_interval);



if __name__ == "__main__":



    if len(sys.argv) == 1:
        exit(-1);
        
    try:
        main_pid = int(sys.argv[1]);
    except:
        exit(-2);
    

    run_guardian(main_pid);
