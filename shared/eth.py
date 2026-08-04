from shared.utils      import read_json;
from shared.time_utils import unix_to_localstr, get_str_today, str_to_unix;
from shared.config     import CONFIG_JSON, LOCAL_JSON, PUBLIC_KEY_PATH, DEVICE_ID;

from shared.encrypt    import encrypt_file;

import dropbox;
import os;
import json;






config = read_json(CONFIG_JSON);

dbx = dropbox.Dropbox(
    oauth2_refresh_token=config["refresh_token"],
    app_key=config["app_key"],
    app_secret=config["app_secret"]
);


def PATH(device_id, *parts):
    return "/" + device_id + "/" + "/".join(parts)

# basic api

def get_file_bytes(path):
    try:
        metadata, response = dbx.files_download(f"{path}");
        data = response.content;
        return data;
    except:
        return None;

def upload_file_bytes(bytes, dest_path: str):
    try:
        dbx.files_upload(
            bytes,
            dest_path,
            mode=dropbox.files.WriteMode.overwrite
        );
    except:
        return -1;
    
    return 0;

def get_folder_content(folder_path):
    try:
        result = dbx.files_list_folder(folder_path)
    except:
        return [];

    content = [];

    while True:
        for entry in result.entries:
            
            if isinstance(entry, dropbox.files.FileMetadata):
                content.append(("file", entry.name));
            elif isinstance(entry, dropbox.files.FolderMetadata):
                content.append(("folder", entry.name));
            
            #print(entry.name, entry.path_display)
            #content.append(entry.name);
            

        if not result.has_more:
            break

        result = dbx.files_list_folder_continue(result.cursor)

    return content;

def folder_contains(folder_path, searched_type, searched_name): # currently this function is unused 
    try:
        content = get_folder_content(folder_path);
    except:
        return False;
    
    for entry in content:
        entry_type = content[0];
        entry_name = content[1];
        
        if (searched_type == entry_type and searched_name == entry_name):
            return True;
    
    return False;

def delete_folder(path):
    try:
        dbx.files_delete_v2(f"{path}");
    except:
        return -1;
    
    return 0;

def create_folder(path):
    try:
        dbx.files_create_folder_v2(path)
    except:
        return -1;
    return 0;

def upload_file(src_path, dest_path):
    try:
        with open(src_path, mode="rb") as file:
            dbx.files_upload(
                file.read(),
                dest_path,
                mode=dropbox.files.WriteMode.overwrite
            );
    except:
        return -1;
    return 0;

# hidden api

def upload_snapshot(s):
    #today_str = get_str_today();
    #create_folder(today_str);
    
    folder_str      = unix_to_localstr(s["utc"], "%Y-%m-%d");

    # getting screenshot_name

    src_path        = s["screenshot_path"];
    
    screenshot_name = src_path.split('\\')[-1];
    screenshot_name = screenshot_name[:-4]; # deleting ".jpg" at the end

    # getting image bytes

    with open(src_path, mode="rb") as file:
        img_bytes = file.read();
    
    # encrypting image
    
    encrypted_file, encrypted_aes_key = encrypt_file(img_bytes, PUBLIC_KEY_PATH);
    
    # destination paths basically
    
    bin_path = PATH(DEVICE_ID, folder_str, f"{screenshot_name}.bin");
    key_path = PATH(DEVICE_ID, folder_str, f"{screenshot_name}.key");
    
    # uploading
    
    upload_code1 = upload_file_bytes(encrypted_file,    bin_path);
    upload_code2 = upload_file_bytes(encrypted_aes_key, key_path);
    
    if (upload_code1 == 0 and upload_code2 == 0):
        s["sent"] = True;

# public api

    # user api

def push_snapshots(snapshots):
    # передаешь сюда контент из snapshots.json по сути фактически
    
    
    for s in snapshots:
        if (not s["sent"] and os.path.exists(s["screenshot_path"])):
            upload_snapshot(s);

def upload_local():
    dest_path = PATH(DEVICE_ID, "local.json");
    upload_file(LOCAL_JSON, dest_path=dest_path);

    # verifier & user api (shared api)

def get_bins(device_id, date_folder):
    content = get_folder_content(PATH(device_id, date_folder));
    
    if (content is None):
        return [];
    
    images  = [];    
    
    for entry in content:
        entry_type = entry[0];
        entry_name = entry[1];
        
        if (entry_type == "file" and entry_name[-4:] == ".bin"):
            images.append(entry_name);
    
    return images;

def get_date_folders(device_id, date_filter):
    # только один раз вызывается так что норм
    
    content = get_folder_content(f"/{device_id}/");
    
    if (content is None):
        return [];
    
    folders = [entry[1] for entry in content if entry[0] == "folder"];

    sorted_folders = [];

    for folder in folders:
        try:
            timestamp = str_to_unix(folder, "%Y-%m-%d");
            
            if (date_filter is None):
                sorted_folders.append(folder);
            
            if (date_filter is not None and timestamp >= date_filter):
                sorted_folders.append(folder);

        except ValueError:
            # не соответствует формату
            
            continue;

    return sorted_folders;

def get_results_json(device_id, date_folder):
    path       = PATH(device_id, date_folder, "results.json");

    raw        = get_file_bytes(path);
    dictionary = {};
    
    if (raw is not None):
        dictionary = json.loads(raw);
    
    return dictionary;

def get_devices():
    content = get_folder_content("/");
    devices = [entry[1] for entry in content if entry[0] == "folder"];
    return devices;

#   verifier api

def get_status(): # not imported (stored in another file)
    ... # defined in main.py


















