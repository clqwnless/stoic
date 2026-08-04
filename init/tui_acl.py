from shared.acl import reset_permissions, apply_basic_rule, apply_protect_rule;
from shared.cmd import *;

from pathlib import Path



options = """
  options:
  
  cd [index] ; r [index]: reset to default permissions
  cd [path]  ; p [index]: users: (none (no rights)) ; admins: (read & write & execute)
  cd ..      ; b [index]: users are allowed to read but not to write
             ;            (admins: read & write & execute)
  exit       ;            (users:  read & execute)
"""

def get_folder_content(path):
    result = [];

    for item in Path(path).iterdir():
        if item.is_file():
            result.append(("file", item.name, str(item)));
        elif item.is_dir():
            result.append(("folder", item.name, str(item)));

    return result;

def get_parent_dir(path):
    return str(Path(path).parent.resolve());


def get_val(inp_raw, core, type_func):
    try:
        val = type_func(inp_raw[len(core):]);
    except:
        return None;
    return val;

def is_valid_index(items, index):
    if (index is not None and 0 <= index < len(items)):
        return True;
    return False;


def main():
    current_directory = "C:\\";

    

    while True:
        items = get_folder_content(current_directory);
        
        cls();
        
        print(options);
        
        print(f"  {BRIGHT_CYAN}current_directory: {current_directory}{RESET}\n");
        
        for index, item in enumerate(items):
            item_type = item[0];
            item_name = item[1];
            
            if (item_type == "file"):
                item_renderable = f"{BRIGHT_GREEN}[{item_name}]{RESET}";
            elif (item_type == "folder"):
                item_renderable = f"{BRIGHT_YELLOW}[{item_name}]{RESET}";
            
            print(f"  {BRIGHT_RED}[{index}]{RESET} {item_renderable}");
            
            
        inp = input("\n>>> ");
        
        if (inp == "exit"):
            return;
        elif (inp[:3] == "cd "):
            index = get_val(inp, "cd ", int);
            path  = get_val(inp, "cd ", str);

            if (path == ".."):
                current_directory = get_parent_dir(current_directory);
            elif (index is None and os.path.exists(path)):
                current_directory = path;
            elif (is_valid_index(items, index) and (items[index][0] == "folder")):
                folder_path = items[index][2];
                current_directory = folder_path;
        elif (inp[:2] == "r "):
            index = get_val(inp, "r ", int);
            
            if (is_valid_index(items, index)):
                path = items[index][2];
                reset_permissions(path);
                pause();
        elif (inp[:2] == "p "):
            index = get_val(inp, "p ", int);
            
            if (is_valid_index(items, index)):
                path = items[index][2];
                apply_protect_rule(path);
                pause();
        elif (inp[:2] == "b "):
            index = get_val(inp, "b ", int);
            
            if (is_valid_index(items, index)):
                path = items[index][2];
                apply_basic_rule(path);
                pause();



#print(get_val("cd 5s", "cd ", int));


main();

