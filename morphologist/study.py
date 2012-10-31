from collections import defaultdict
import os

class QualityCheck(object):
    UNKNOWN = 0
    VALID = 1
    FAILED = 2
    HANDMADE = 3
    RUNNING = 3

    def __init__(self, analyses_list):
        self.quality_check_per_analysis = {}
        for i in analyses_list:
            self.quality_check_per_analysis[i] = QualityCheck.UNKNOWN


class Subject(object):
    def __init__(self, imgname, subjectname, groupname=None):
        self._imgname = imgname
        self._subjectname = subjectname
        self._groupname = groupname
        self._quality_check_rate = QualityCheck.UNKNOWN


class Study(object):
    def __init__(self, name):
        self._name = name
        self._subjects = []

    def add_subject_from_file(self, filename, groupname=None):
        subjectname = os.path.basename(filename)
        subject = Subject(filename, subjectname, groupname)
        self._subjects.append(subject)

    def add_subjects_from_directory(self, dirname, groupname=None):
        #TODO
        pass
