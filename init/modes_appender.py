from shared.cmd import *;
import os;




options = '''
  delete: d [index] ; m: refresh ; s
'''


def get_exes(folder):
    if (os.path.exists(folder) and os.path.isdir(folder)):
        return [
            f for f in os.listdir(folder)
            if f.lower().endswith(".exe")
        ];

def main():
    current_folder = None;
    
    while True:
        cls();





print(get_exes(r"C:\stoic"));


#print(exe_files);

