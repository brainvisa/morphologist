from __future__ import absolute_import
import os.path
import shutil
# XXX It is necessary to import mock.analysis to register its Analysis classes in AnalysisFactory
from . import mocks.analysis

def reset_directory(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)

def remove_file(file_name):
    if os.path.isfile(file_name):
        os.remove(file_name)


