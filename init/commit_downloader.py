from shared.cmd    import *;
from shared.git    import *;
from shared.utils  import get_val;
from shared.config import UPDATES_CACHE_DIR;


OWNER = "clqwnless"; 
REPO  = "stoic";



semicolon = f"{YELLOW};{RESET}";

options = f"""
  x: {BRIGHT_GREEN}next{RESET} {semicolon} z: {BRIGHT_GREEN}prev{RESET} {semicolon} exit {semicolon} d {BRIGHT_RED}[index]{RESET}: {BRIGHT_GREEN}download{RESET}
"""


def render_metainfo(repo, page):
    print(f"  owner = {BRIGHT_RED}{repo.owner}{RESET}");
    print(f"  repo  = {BRIGHT_GREEN}{repo.name}{RESET}\n");
    
    print(f"  current_page = {BRIGHT_GREEN}{page}{RESET}\n");
    
def render_commits(commits):
    print(f"  {BRIGHT_MAGENTA}commits{RESET}:\n");
    
    for index, commit in enumerate(commits):
        message, time_str = get_commit_metainfo(commit);
        print(f"  {BRIGHT_CYAN}[{index}]{RESET} {YELLOW}[{time_str}]{RESET} {BRIGHT_GREEN}[{message}]{RESET}");

def commits_mode(repo):
    commits = {};
    page    = 1;

    commits[page] = get_commits(repo, page);

    while True:
        cls();

        print(options);

        render_metainfo(repo, page);

        # rendering commits

        render_commits(commits[page]);

        inp = input("\n>>> ");
        if (inp == "exit"):
            return;

        if (inp == "x"):
            page += 1;
        if (page not in commits):
            commits[page] = get_commits(repo, page);
        elif (inp == "z" and page > 1):
            page -= 1;
        elif (inp[:2] == "d "):
            index = get_val(inp, "d ", int);
            
            if (index is None):
                continue;
            
            commit = commits[page][index];
            
            process_commit(repo, UPDATES_CACHE_DIR, commit);
            pause();




if __name__ == "__main__":
    r = Repository(
        owner=OWNER,
        name=REPO
    );

    commits_mode(r);
