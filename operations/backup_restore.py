import shutil
import os
import shutil
from datetime import datetime
import time

def backup(root_in = "volumes", root_out = "backup"):
    # list_file = os.listdir(root_out)
    # if len(list_file) == 0:
    now = datetime.now() # current date and time
    time.sleep(5)
    date_time = now.strftime("%m_%d_%Y_%H_%M_%S_backup")
    name_file_out = date_time
    path_out = os.path.join(root_out, name_file_out)
    shutil.make_archive(path_out, format='zip', root_dir=root_in)
    
def restore(root_in = "backup", root_out = "volumes", name_backup=None):
    backup(root_out, root_in)
    path_in = os.path.join(root_in, name_backup)
    shutil.rmtree(root_out)
    shutil.unpack_archive(path_in, root_out)
     
def get_newest_database(root = "backup"):
    for i, name in enumerate(os.listdir(root)):
        name = name[:-4]
        print(name)
        if i == 0:
            newest_time = datetime.strptime(name, '%m_%d_%Y_%H_%M_%S_backup')
        else:
            date = datetime.strptime(name, '%m_%d_%Y_%H_%M_%S_backup')
            if date > newest_time:
                newest_time = date
    return newest_time
    
