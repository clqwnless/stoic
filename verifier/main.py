


from PySide6.QtCore import Qt;
from PySide6.QtGui import QPixmap, QAction, QShortcut, QKeySequence;
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMenu
)



from shared.eth     import get_folder_content, get_file_bytes, upload_file_bytes, delete_folder, get_date_folders, get_bins;
from shared.decrypt import decrypt_file;
from shared.config  import PRIVATE_KEY_PATH;

from shared.cmd     import *;



import json;
import time;
import os;
import builtins;
import sys;
import traceback;


from datetime import datetime;


# term ansi sequences


# global variables (defined at the start)

images_storage  = {};
folders_storage = {};

status          = None;
device_id       = None;
date_filter     = None;

total_bins      = 0;


# called on start

def save_images_to_ram():
    global images_storage;
    
    
    folders = get_allowed_folders();
    counter = 0;

    print(f"\n{BRIGHT_RED}TOTAL_BINS={total_bins}{RESET}");

    for folder in folders:
        binaries = get_allowed_files(folder);
        
        print(f"\nFolder: {folder}\n")
        
        for binary in binaries:
            binary_name = binary[:-4]; # removing ".bin"
            
            bin_path = PATH(folder, binary);
            key_path = PATH(folder, f"{binary_name}.key");

            done_percent = (counter / total_bins) * 100;

            print(f"Saving: {bin_path}, {BRIGHT_GREEN}done_percent={done_percent:.1f}{RESET}");



            bin_bytes = get_file_bytes(bin_path);
            key_bytes = get_file_bytes(key_path);
            
            decrypted_image = decrypt_file(bin_bytes, key_bytes, PRIVATE_KEY_PATH);
            
            images_storage[bin_path] = decrypted_image;
            
            counter += 1;

def save_folders_to_ram():
    folders = get_date_folders(device_id, date_filter);
    
    print(f"\n{BRIGHT_RED}TOTAL_FOLDERS={len(folders)}{RESET}\n");
    
    for folder in folders:
        binaries = get_bins(device_id, folder);

        print(f"Saving folder to ram: {folder}");
        
        obj = {};
        obj["bins"]   = binaries;

        folders_storage[folder] = obj;


# hidden api
 
def get_status():
    status_path = PATH("local.json");
    
    status_raw  = get_file_bytes(status_path);
    status_raw  = status_raw.decode("utf-8");
    status      = json.loads(status_raw);

    return status;

# ...

# public api

def get_allowed_files(folder):
    if (folder in folders_storage):
        return folders_storage[folder]["bins"];
    return [];

def get_allowed_folders():
    return folders_storage.keys();

def get_results():
    results = {};
    
    for folder in get_allowed_folders(): 
        folder_content = get_folder_content(PATH(folder));
        found_results = False;
        
        for entry in folder_content:
            entry_type = entry[0];
            entry_name = entry[1];
            
            if (entry_type == "file" and entry_name == "results.json"):
                found_results = True;
                break;
        
        if (found_results):
            results_path = PATH(folder, "results.json");
            
            results_raw  = get_file_bytes(results_path);
            results_raw  = results_raw.decode("utf-8");
            
            results_json = json.loads(results_raw);
            
            results[folder] = results_json["files"];
    
    return results;

def get_image(folder, file):
    if (file == ""):
        return;
    
    #print(f"folder=\"{folder}\", file=\"{file}\"");
    
    img_path = PATH(folder, file);
    image_raw = images_storage[img_path];
    
    pixmap = QPixmap()
    pixmap.loadFromData(image_raw)
    
    return pixmap;

def get_metadata(folder, file):

    # später:
    # requests.get(...)
    # return response.json()
    
    # имя у файла по сути utc формат - поэтому можно прямо в int конвертировать (ну допущение такое)

    # getting file utc
    
    
    without_jpg = file[:-4]
    file_utc = int(without_jpg);
    
    if (file == "" or file_utc is None):
        return None;
    
    # searching for task
    
    
    event = find_task_by_timestamp(file_utc);

    if (event is not None):
        return {"task": event["task"]}
    return {"task": None};

def count_total_bins():
    total = 0;
    
    for folder in get_allowed_folders():
        total += len(get_bins(device_id, folder));
    
    return total;


# path

def PATH(*parts):
    return "/" + device_id + "/" + "/".join(parts)

# requesting device_ids

def cls():
    os.system("cls");

def pause():
    os.system("pause");

def int(value) -> int | None:
    try:
        return builtins.int(value)
    except (ValueError, TypeError):
        return None;



# ==========================================================


class MainWindow(QMainWindow):

    def __init__(self):
        # data

        self.results = get_results()

        self.current_folder = None
        self.current_file   = None

        self.delete_queue   = [];


        # interface

        super().__init__()

        self.setWindowTitle("Dropbox Review")
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        #######################################################
        # Labels
        #######################################################

        self.status_label = QLabel("Status: UNDEFINED")
        self.info_label = QLabel("Explanation: None")

        self.status_label.setWordWrap(True)
        self.info_label.setWordWrap(True)

        #######################################################
        # LEFT (Folders)
        #######################################################

        left = QVBoxLayout()

        folder_title = QLabel("Folders")
        folder_title.setAlignment(Qt.AlignCenter)

        self.folder_list = QListWidget()
        self.folder_list.addItems(get_allowed_folders())
        self.folder_list.currentTextChanged.connect(
            self.folder_changed
        )

        # Context menu

        self.folder_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        self.folder_list.customContextMenuRequested.connect(
            self.show_folder_menu
        )

        # Folder buttons

        folder_buttons = QHBoxLayout()

        self.restore_folders_button = QPushButton("Restore")
        self.save_folders_button = QPushButton("Save")
        
        self.save_folders_button.setObjectName("folderSaveButton")

        self.restore_folders_button.clicked.connect(
            self.restore_folders
        )

        self.save_folders_button.clicked.connect(
            self.save_folders
        )

        #self.restore_folders_button.setEnabled(False)
        #self.save_folders_button.setEnabled(False)

        folder_buttons.addWidget(
            self.restore_folders_button
        )

        folder_buttons.addWidget(
            self.save_folders_button
        )

        left.addWidget(folder_title)
        left.addWidget(self.folder_list)
        left.addLayout(folder_buttons)

        #######################################################
        # CENTER (Files)
        #######################################################

        self.file_list = QListWidget()
        self.file_list.currentTextChanged.connect(
            self.file_changed
        )

        #######################################################
        # RIGHT
        #######################################################

        right = QVBoxLayout()

        # Image

        self.image = QLabel("No Image")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(900, 500)

        # Comment

        self.comment = QTextEdit()
        self.comment.setPlaceholderText("Explanation...")

        # Buttons

        self.ok_button = QPushButton("OK")
        self.not_ok_button = QPushButton("NOT OK")

        self.ok_button.clicked.connect(self.save_ok)
        self.not_ok_button.clicked.connect(self.save_not_ok)

        # Save results

        self.save_button = QPushButton("SAVE")
        self.save_button.clicked.connect(
            self.save_to_server
        )

        self.save_button.setObjectName("saveButton")

        # Meta

        self.meta_label = QLabel("task: none")
        self.meta_label.setWordWrap(True)

        # Add widgets

        right.addWidget(self.image, 1)

        right.addWidget(self.status_label)
        right.addWidget(self.info_label)

        right.addWidget(self.comment)

        right.addWidget(self.ok_button)
        right.addWidget(self.not_ok_button)

        right.addWidget(self.save_button)

        right.addWidget(self.meta_label)

        #######################################################
        # MAIN LAYOUT
        #######################################################

        layout.addLayout(left, 1)
        layout.addWidget(self.file_list, 1)
        layout.addLayout(right, 5)

        #######################################################
        # Shortcuts
        #######################################################

        QShortcut(
            QKeySequence("Z"),
            self,
            activated=self.shortcut_ok
        )

        QShortcut(
            QKeySequence("X"),
            self,
            activated=self.shortcut_not_ok
        )

        QShortcut(
            QKeySequence("C"),
            self,
            activated=self.shortcut_comment
        )

        QShortcut(
            QKeySequence("Esc"),
            self.comment,
            activated=self.folder_list.setFocus
        )

        QShortcut(
            QKeySequence(Qt.Key_Down),
            self,
            activated=self.next_file
        )

        QShortcut(
            QKeySequence(Qt.Key_Up),
            self,
            activated=self.previous_file
        )

        #######################################################
        # Style
        #######################################################

        self.setStyleSheet("""
        * {
            background: #202020;
            color: white;
            font-family: Consolas;
            font-size: 11pt;
        }

        QListWidget {
            background: #2b2b2b;
        }

        QTextEdit {
            background: #2b2b2b;
        }

        QPushButton {
            background: #404040;
            min-height: 35px;
        }

        QPushButton:hover {
            background: #555555;
        }

        QLabel {
            background: black;
            border: 1px solid #555;
        }

        QPushButton#saveButton {
            background: #2e6b3a;
        }

        QPushButton#saveButton:hover {
            background: #3f8b4d;
        }
        
        QPushButton#folderSaveButton {
            background: #8a5b1f;
        }

        QPushButton#folderSaveButton:hover {
            background: #a66d24;
        }
        
        """)

    @property
    def current_file_in_results(self):
        return (self.current_folder in self.results) and (self.current_file in self.results[self.current_folder]);

    @property
    def current_file_result(self):
        return self.results[self.current_folder][self.current_file];


    ###########################################################

    def save_to_server(self):
        # форматируем данные в приемлимый формат

        # uploading to the server

        for folder, files_metadata in self.results.items():
            
            status = {
                "utc":   get_current_time(),
                "files": files_metadata
            }
            
            json_str   = json.dumps(status, indent=4);
            json_bytes = json_str.encode("utf-8");
            
            dest_path  = PATH(folder, "results.json");

            upload_file_bytes(json_bytes, dest_path);


    
    # left buttons
    
    def restore_folders(self):
        self.delete_queue.clear();
        
        self.folder_list.clear();
        self.folder_list.addItems(get_allowed_folders());
    
    def save_folders(self):
        for q in self.delete_queue:
            # deleting in folder storage
            
            del folders_storage[q["folder_name"]];
            
            # deleting on the server
            
            delete_folder(q["folder_path"]);
        
        # clearing the queue
        
        self.delete_queue.clear();




    # bindings

    def typing(self):
        return self.comment.hasFocus()

    def shortcut_ok(self):

        if self.typing():
            return

        self.save_ok()

    def shortcut_not_ok(self):

        if self.typing():
            return

        self.save_not_ok()

    def shortcut_comment(self):

        if self.typing():
            return

        self.comment.setFocus()

    def next_file(self):

        row = self.file_list.currentRow()

        if row < self.file_list.count() - 1:
            self.file_list.setCurrentRow(row + 1)

    def previous_file(self):

        row = self.file_list.currentRow()

        if row > 0:
            self.file_list.setCurrentRow(row - 1)




    def delete_folder(self, item):

        folder = item.text()
        
        #print("Delete:", folder)

        folder_path = f"/{folder}";

        queue_object = {
            "folder_path":  folder_path,
            "folder_name":  folder
        }

        self.delete_queue.append(queue_object);
        
        #print(self.delete_queue);

        row = self.folder_list.row(item)
        self.folder_list.takeItem(row)


    def show_folder_menu(self, pos):

        item = self.folder_list.itemAt(pos)

        if item is None:
            return

        menu = QMenu(self)

        delete_action = QAction("Delete", self)
        menu.addAction(delete_action)

        action = menu.exec(
            self.folder_list.mapToGlobal(pos)
        )

        if action == delete_action:
            self.delete_folder(item)


    def clear_image(self):
        self.image.clear()
        self.image.setText("no image")

        self.status_label.setText("Status: UNDEFINED")
        self.comment.setText("Explanation: None")

        self.comment.clear()


    def update_info(self):

        if self.current_file is None:
            return

        if self.current_file_in_results:

            data = self.results[self.current_folder][self.current_file];
            self.status_label.setText(f"Status: {data['status']}")
            text = data["comment"]

            if not text:
                text = "None"

            self.info_label.setText(f"Explanation: {text}")

        else:

            self.status_label.setText("Status: UNDEFINED")

            self.info_label.setText("Explanation: None")

    def folder_changed(self, folder):

        self.current_folder = folder

        self.file_list.clear()

        files = get_allowed_files(folder)

        self.file_list.addItems(files)
        
        self.clear_image();
        
        self.meta_label.setText("task: none");
        
        self.current_file = None;

    ###########################################################

    def file_changed(self, file):
        self.current_file = file

        image = get_image(self.current_folder, self.current_file)

        if isinstance(image, QPixmap):

            self.image.setPixmap(
                image.scaled(
                    self.image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

        self.update_info()
        
        
        if (self.current_file_in_results):
            self.comment.setPlainText(self.current_file_result["comment"])
        else:
            self.comment.clear()

        meta = get_metadata(self.current_folder, self.current_file);

        if (meta is not None):
            self.meta_label.setText(f"task: {meta['task']}")


    ###########################################################

    def save(self, status):


        if self.current_file is None:
            return;

        if (self.current_folder not in self.results):
            self.results[self.current_folder] = {};
        
        obj = {};
        obj["status"]    = status;
        obj["comment"]   = self.comment.toPlainText();
        
        self.results[self.current_folder][self.current_file] = obj;

        self.update_info()

        #print(self.results)

    ###########################################################

    def save_ok(self):
        self.save("OK")

    ###########################################################

    def save_not_ok(self):
        self.save("NOT OK")






try:
    # saving device_id

    device_id      = request_device();

    if (device_id is None):
        exit(0);

    # getting date filter

    date_filter = request_date_filter();

    # status

    status = get_status();

    # folders

    save_folders_to_ram();

    # total bins

    total_bins = count_total_bins(); # иначе потом ZeroDivisionError будет поскольку там в save_images_to_ram делится а у меня инициальное значение на нуле

    # images

    save_images_to_ram();
except BaseException as e:
    tb = traceback.format_exc()
    
    print(tb);
    
    with open("crash.log", mode="w") as file:
        file.write(tb);

    pause();

    exit(-1);
    




# app


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()


