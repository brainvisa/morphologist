import os.path
import shutil


def reset_directory(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)

def remove_file(file_name):
    if os.path.isfile(file_name):
        os.remove(file_name)


