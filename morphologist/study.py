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
        self.imgname = imgname
        self.subjectname = subjectname
        self.groupname = groupname
        self.quality_check_rate = QualityCheck.UNKNOWN

    def __repr__(self):
        s = '\t<imgname: ' + str(self.imgname) + ',\n'
        s += '\tsubjectname: ' + str(self.subjectname) + ',\n'
        s += '\tgroupname: ' + str(self.groupname) + ',\n'
        s += '\tquality_check_rate: ' + str(self.quality_check_rate) + '>\n'
        return s

class Study(object):
    def __init__(self, name="undefined study", outputdir=None):
        self.name = name
        self.outputdir = outputdir
        self.subjects = []

    @classmethod
    def define_subjectname_from_filename(self, filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def add_subject_from_file(self, filename, subjectname=None, groupname=None):
        if subjectname is None:
            subjectname = self.define_subjectname_from_filename(subjectname)
        subject = Subject(filename, subjectname, groupname)
        self.subjects.append(subject)

    def __repr__(self):
        s = 'name :' + str(self.name) + '\n'
        s += 'outputdir :' + str(self.outputdir) + '\n'
        s += 'subjects :' + repr(self.subjects) + '\n'
        return s
