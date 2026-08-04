import os;


# alias for os.system
def execute(command: str):
    os.system(command);

def reset_permissions(path):
    execute(f'icacls "{path}" /reset /T')
    execute(f'icacls "{path}" /inheritance:e /T /C');

def apply_basic_rule(path, log=True):
    recursive = " /T" if os.path.isdir(path) else "";
    
    logging   = "" if log else " > nul 2>&1"; 
    
    # отключаем наследование
    
    execute(f"icacls \"{path}\" /inheritance:r{recursive}{logging}");
    
    # даём админу полные права
    
    execute(f"icacls \"{path}\" /grant Administrators:F{recursive}{logging}");
    
    # даём обычным юзерам только execute & read права
    
    execute(f"icacls \"{path}\" /grant Users:RX{recursive}{logging}");


'''
def apply_protect_rule(file_path):
    execute(f"icacls \"{file_path}\" /inheritance:r");
    execute(f"icacls \"{file_path}\" /remove Users");
    execute(f"icacls \"{file_path}\" /grant Administrators:F");
'''

def apply_protect_rule(path):
    suffix = " /T" if os.path.isdir(path) else "";

    execute(f'icacls "{path}" /inheritance:r{suffix}');
    execute(f'icacls "{path}" /remove:g Users{suffix}');
    execute(f'icacls "{path}" /remove:g "Authenticated Users"{suffix}');
    execute(f'icacls "{path}" /grant:r Administrators:F{suffix}');
    execute(f'icacls "{path}" /grant:r SYSTEM:F{suffix}');


def PATH(*args):
    return os.path.join(*args);
 

