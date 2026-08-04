from shared.acl     import reset_permissions, apply_basic_rule, apply_protect_rule;
from shared.config  import ROOT_PATH, EXTENSIONS_JSON, DB_PATH, PATH;
from shared.utils   import read_json;

import os;

def get_choice(info):
    while True:
        inp = input(info).lower();
        
        if (inp == "x"):
            exit(0);
        
        if (inp == 'y'):
            return True;
        
        if (inp == 'n'):
            return False;


def get_extensions(): 
    try:
        extensions = read_json(EXTENSIONS_JSON);
    except:
        return [];
    return extensions;


c1 = get_choice("Reset All Permisions (extensions, database folder, root)? (y/n)\n>>> ");
c2 = get_choice("Apply Basic Rule (users: execute & read) ; (admin: write, ..., all rights)? (y/n)\n>>> ");
c3 = get_choice("Apply Basic Rule for DataBase Folder? (y/n)\n>>> ");
c4 = get_choice("Protect private.py (admin_name & admin_pass)? (y/n)\n>>> ");
c5 = get_choice("Apply Basic Rule for extensions? (y/n)\n>>> ");


if (c1):
    reset_permissions(ROOT_PATH);
    reset_permissions(DB_PATH);
    
    # resetting extensions
    
    extensions = get_extensions();
    for ext in extensions:
        reset_permissions(ext["entry_point"]);
    

if (c2):
    apply_basic_rule(ROOT_PATH);

if (c3):
    apply_basic_rule(DB_PATH);
    #apply_protect_rule(DB_PATH);

if (c4):
    private_py_path = PATH(ROOT_PATH, "user_service", "private.py");
    apply_protect_rule(private_py_path);

if (c5):
    extensions = read_json(EXTENSIONS_JSON);
    
    for ext in extensions:
        apply_basic_rule(ext["entry_point"]);

