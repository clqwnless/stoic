from shared.cmd import *;
from shared.acl import apply_protect_rule;

from .winapi    import get_admin_group;


import subprocess;
import secrets;

# globals

PASSWORDS_FILE = f"passwords.txt";
PASS_LENGTH    = 8;

menu = """
's' [index]: set ; 'w' [index] : unset ; 'x': (exit) ; 'push' ; protect_pass_file
"""

# functions

def generate_pass():
    return secrets.token_hex(int(PASS_LENGTH / 2));

def change_pass(user_name, password):
    args = [
        "net",
        "user",
        user_name,
        password
    ];
    
    res = subprocess.run(args, shell=True);
    
    return res;

def protect_pass_file():
    apply_protect_rule(PASSWORDS_FILE);
    
    print();
    pause();

def push():
    passwords = {};
    
    
    print();
    for user in users:
        user_name = user["name"];
        
        if (not user["pending"]):
            print(f"  {BRIGHT_RED}Skipping: {user_name}{RESET}");
            continue;
        
        password = generate_pass();
        res      = change_pass(user_name, password);

        if (res.returncode == 0):
            passwords[user_name] = password;

    print(f"\n{BRIGHT_GREEN}Saving passwords to the file: {PASSWORDS_FILE}{RESET}");
    
    if passwords:
        with open(PASSWORDS_FILE, mode="w") as file:
            for user_name, password in passwords.items():
                file.write(f"{user_name} {password}");
    
    print(f"\n{BRIGHT_CYAN}DONE{RESET}\n");
    
    pause();

def main():
    while True:
        cls();
        
        print(menu);
        
        for index, user in enumerate(users):
            
            index_str   = f"{BRIGHT_CYAN}{index}{RESET}";
            pending_str = f"{BRIGHT_GREEN}X{RESET}" if user["pending"] else f"{BRIGHT_RED}X{RESET}";
            user_str    = f"{BRIGHT_GREEN}{user["name"]}{RESET}";
            
            
            print(f"  [{index_str}] [{pending_str}] [{user_str}]");

        inp = input("\n>>> ").lower();
        

        if (inp == "x"):
            return;
        elif (inp == "push"):
            push();
        elif (inp == "protect_pass_file"):
            protect_pass_file();
        elif (inp[:2] == "s "):
            try:
                index = int(inp[2:]);
            except:
                continue;
            
            if not (0 <= index < len(users)):
                continue;
            
            users[index]["pending"] = True;
        elif (inp[:2] == "w "):
            try:
                index = int(inp[2:]);
            except:
                continue;
            
            if not (0 <= index < len(users)):
                continue;
            
            users[index]["pending"] = False;


# getting the users

users = [{"name": admin_name, "pending": False} for admin_name in get_admin_group()];

# main

main();

