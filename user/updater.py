from shared.git    import *;
from shared.cmd    import *;
from shared.utils  import get_val;
from shared.config import PENDING_UPDATE_FILE;

from init       import commit_downloader;

from pathlib import Path;

import json;
import os;

OWNER = "clqwnless";
REPO  = "stoic";

semicolon = f"{YELLOW};{RESET}";

options   = f"""
c: {BRIGHT_GREEN}next{RESET} {semicolon} v: {BRIGHT_GREEN}prev{RESET} {semicolon} x: {BRIGHT_GREEN}exit{RESET} {semicolon} u {BRIGHT_RED}[index]{RESET}: {BRIGHT_GREEN}set pending update{RESET}
""";


def set_pending(commit):
    parent = Path(PENDING_UPDATE_FILE).resolve().parent;

    commit_bytes = json.dumps(commit, indent=4, ensure_ascii=False).encode("utf-8");

    with open(PENDING_UPDATE_FILE, mode="wb") as file:
        file.write(commit_bytes);

def main(repo):
    commits = {};
    page    = 1;

    commits[page] = get_commits(repo, page);

    while True:
        cls();

        print(options);

        commit_downloader.render_metainfo(repo, page);

        # rendering commits

        commit_downloader.render_commits(commits[page]);

        inp = input("\n>>> ");
        if (inp == "x"):
            return;
        
        if (inp == "c"):
            page += 1;
            
            if (page not in commits):
                commits[page] = get_commits(repo, page);
        
        
        elif (inp == "v" and page > 1):
            page -= 1;
        elif (inp[:2] == "u "):
            index = get_val(inp, "u ", int);
            
            if (index is None):
                continue;

            commit = commits[page][index];
            set_pending(commit);
            
            print("ok\n");
            
            pause();

def get_repo():
    return Repository(
        owner=OWNER,
        name=REPO
    );

def start():
    main(get_repo());


if __name__ == "__main__":
    start();

