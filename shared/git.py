from shared.time_utils import *;
from datetime          import datetime;
from dataclasses       import dataclass;

import requests;
import zipfile;
import io;
import os;

@dataclass
class Repository:
    owner: str;
    name:  str;

# (private/public api)

def download_commit(repo, commit):
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/zipball/{commit["sha"]}";
    r   = requests.get(url);
    
    zip_bytes = r.content;
    return zip_bytes;

def unzip_cached_commit(zip_bytes, path):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        z.extractall(path);

def get_commit_metainfo(commit, time_format="%Y-%m-%d %H:%M"):
    message  = commit["commit"]["message"];
    date     = commit["commit"]["committer"]["date"];
    
    dt       = datetime.fromisoformat(date.replace("Z", "+00:00"))
    time_str = unix_to_localstr(int(dt.timestamp()), fmt=time_format);

    return message, time_str;

# public api

def get_commits(repo, page):
    #headers = {"Authorization": f"Bearer {TOKEN}"};

    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/commits";

    params  = {"per_page": 100, "page": page};
    
    r = requests.get(
        url=url,
        #headers=headers,
        params=params
    );
    
    commits = r.json();

    return commits;

def process_commit(repo, dest_path, commit):
    zip_bytes = download_commit(repo, commit);
    
    message, time_str = get_commit_metainfo(commit, time_format="%Y-%m-%d-%H-%M");
    #file_name = time_str + '_' + message;
    file_name = time_str;
    
    path = os.path.join(dest_path, file_name);
    
    unzip_cached_commit(zip_bytes, path);
    
    return path;

