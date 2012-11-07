from collections import defaultdict
import os



class Subject(object):

    def __init__(self, imgname, subjectname, groupname=None):
        self.imgname = imgname
        self.subjectname = subjectname
        self.groupname = groupname

    def __repr__(self):
        s = '\t<imgname: ' + str(self.imgname) + ',\n'
        s += '\tsubjectname: ' + str(self.subjectname) + ',\n'
        s += '\tgroupname: ' + str(self.groupname) + ',\n'
        return s


class Study(object):
    default_outputdir = os.path.join(os.getcwd(), '.morphologist/studies/study')

    def __init__(self, name="undefined study", outputdir=default_outputdir):
        self.name = name
        self.outputdir = outputdir
        self.subjects = []
        self._analysis = None

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
