import subprocess;


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


