from shared.cmd        import *;
from shared.time_utils import *;
from shared.config     import UPDATES_CACHE_DIR;

from datetime          import datetime;

import requests;
import os;
import zipfile;
import json;
import io;

OWNER = "clqwnless"; 
REPO  = "stoic";



semicolon = f"{YELLOW};{RESET}";

options = f"""
  x: {BRIGHT_GREEN}next{RESET} {semicolon} z: {BRIGHT_GREEN}prev{RESET} {semicolon} exit {semicolon} d {BRIGHT_RED}[index]{RESET}: {BRIGHT_GREEN}download{RESET} ; r: {BRIGHT_GREEN}releases{RESET}, c: {BRIGHT_GREEN}commits{RESET}
"""


def get_repo_info(page, request):
    #headers = {"Authorization": f"Bearer {TOKEN}"};
    
    if (request == "commits"):
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits";
    elif (request == "releases"):
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases";
    else:
        return;

    params  = {"per_page": 100, "page": page};
    
    r = requests.get(
        url=url,
        #headers=headers,
        params=params
    );
    
    commits = r.json();

    return commits;

    


def download_commit(commit):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/zipball/{commit["sha"]}";
    r   = requests.get(url);
    
    zip_bytes = r.content;
    return zip_bytes;

def unzip_cached_commit(zip_bytes, path):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        z.extractall(path);

def process_commit(commit):
    zip_bytes = download_commit(commit);
    
    print(zip_bytes);
    
    message, time_str = get_commit_metainfo(commit, time_format="%Y-%m-%d-%H-%M");
    #file_name = time_str + '_' + message;
    file_name = time_str;
    
    path = os.path.join(UPDATES_CACHE_DIR, file_name);
    
    unzip_cached_commit(zip_bytes, path);

def get_commit_metainfo(commit, time_format="%Y-%m-%d %H:%M"):
    message  = commit["commit"]["message"];
    date     = commit["commit"]["committer"]["date"];
    
    dt       = datetime.fromisoformat(date.replace("Z", "+00:00"))
    time_str = unix_to_localstr(int(dt.timestamp()), fmt=time_format);

    return message, time_str;




def render_metainfo(page):
    print(options);
    print(f"  owner = {BRIGHT_RED}{OWNER}{RESET}");
    print(f"  repo  = {BRIGHT_GREEN}{REPO}{RESET}\n");
    
    print(f"  current_page = {BRIGHT_GREEN}{page}{RESET}\n");
    


def commits_mode():
    commits = {};
    page    = 1;

    commits[page] = get_repo_info(page, request="commits");

    while True:
        cls();

        render_metainfo(page);

        # rendering commits

        print(f"  {BRIGHT_MAGENTA}commits{RESET}:\n");
        
        for index, commit in enumerate(commits[page]):
            message, time_str = get_commit_metainfo(commit);
            print(f"  {BRIGHT_CYAN}[{index}]{RESET} {YELLOW}[{time_str}]{RESET} {BRIGHT_GREEN}[{message}]{RESET}");


        inp = input("\n>>> ");
        if (inp == "exit"):
            return "exit";
        elif (inp == "r"):
            return "releases";

        if (inp == "x"):
            page += 1;
        if (page not in commits):
            commits[page] = get_repo_info(page, request="commits");
        elif (inp == "z" and page > 1):
            page -= 1;
        elif (inp[:2] == "d "):
            try:
                index = int(inp[2:]);
            except:
                continue; 
                
            process_commit(commits[page][index]);
            pause();

def releases_mode():
    ...




def main():
    mode = "commits";
    
    while True:
        if (mode == "commits"):
            mode = commits_mode();
        elif (mode == "releases"):
            mode = releases_mode();
        elif (mode == "exit"):
            return;




main();
