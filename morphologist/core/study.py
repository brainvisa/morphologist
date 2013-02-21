import os
import json

from morphologist.core.analysis import InputParameters, OutputParameters, ImportationError


class Subject(object):
    DEFAULT_GROUP = "group1"
    
    def __init__(self, groupname, subjectname, filename):
        self.groupname = groupname
        self.subjectname = subjectname
        self.filename = filename
        
    def id(self):
        return self.groupname + "-" + self.subjectname
        
    def __repr__(self):
        s = "(%s, %s, %s)" % (self.groupname, self.subjectname, self.filename)
        return s

    def __str__(self):
        return self.id()
    
    def __hash__(self):
        return hash(self.id())
    
    def __cmp__(self, other):
        return cmp(self.id(), other.id())
        
    def serialize(self):
        serialized = {}
        serialized['filename'] = self.filename
        serialized['groupname'] = self.groupname
        serialized['subjectname'] = self.subjectname
        return serialized

    @classmethod
    def unserialize(cls, serialized):
        subject = cls(groupname=serialized['groupname'],
                      subjectname=serialized['subjectname'], 
                      filename=serialized['filename'])
        return subject


class Study(object):
    default_outputdir = os.path.join(os.path.expanduser("~"),
                                'morphologist/studies/study')
    
    def __init__(self, name="undefined study",
        outputdir=default_outputdir, backup_filename=None):
        self.name = name
        self.outputdir = outputdir
        self.subjects = []
        self.analyses = {}
        if backup_filename is None:
            backup_filename = self.default_backup_filename_from_outputdir(outputdir)
        self.backup_filename = backup_filename

    @staticmethod
    def default_backup_filename_from_outputdir(outputdir):
        return os.path.join(outputdir, 'study.json')

    @staticmethod
    def default_outputdir_from_backup_filename(backup_filename):
        return os.path.dirname(backup_filename)

    @classmethod
    def from_file(cls, backup_filename):
        try:
            with open(backup_filename, "r") as fd:
                    serialized_study = json.load(fd)
        except Exception, e:
            raise StudySerializationError("%s" %(e))

        try:
            study = cls.unserialize(serialized_study)
            study.backup_filename = backup_filename
        except KeyError, e:
            raise StudySerializationError("The information does not "
                                          "match with a study.")
        return study

    @classmethod
    def unserialize(cls, serialized):
        study = cls(name=serialized['name'],
                    outputdir=serialized['outputdir'])
        for serialized_subject in serialized['subjects']:
            study.subjects.append(Subject.unserialize(serialized_subject))
        for subject in study.subjects:
            subject_id = subject.id()
            if subject_id not in serialized['inputs']:
                raise StudySerializationError("Cannot find input params"
                                         " for subject %s" % str(subject))
            if subject_id not in serialized['outputs']:
                raise StudySerializationError("Cannot find output params" 
                                         " for subject %s" % str(subject))
            serialized_inputs = serialized['inputs'][subject_id] 
            serialized_outputs = serialized['outputs'][subject_id]
            inputs = InputParameters.unserialize(serialized_inputs) 
            outputs = OutputParameters.unserialize(serialized_outputs)
            analysis = cls._create_analysis()
            analysis.inputs = inputs
            analysis.outputs = outputs
            # TODO => check if the parameters are compatibles with the analysis ?
            study.analyses[subject_id] = analysis
        return study

    def save_to_backup_file(self):
        serialized_study = self.serialize()
        try:
            with open(self.backup_filename, "w") as fd:
                json.dump(serialized_study, fd, indent=4, sort_keys=True)
        except Exception, e:
            raise StudySerializationError("%s" %(e))
  
    def serialize(self):
        serialized = {}
        serialized['name'] = self.name
        serialized['outputdir'] = self.outputdir
        serialized['subjects'] = []
        for subject in self.subjects:
            serialized['subjects'].append(subject.serialize())
        serialized['inputs'] = {}
        serialized['outputs'] = {}
        for subject_id, analysis in self.analyses.iteritems():
            serialized['inputs'][subject_id] = analysis.inputs.serialize()
            serialized['outputs'][subject_id] = analysis.outputs.serialize()
        return serialized 

    @staticmethod
    def define_subjectname_from_filename(filename):
        return remove_all_extensions(filename)

    def add_subject(self, subject):
        if subject in self.subjects:
            raise SubjectExistsError(subject)
        self.subjects.append(subject)
        self.analyses[subject.id()] = self._create_analysis()
        
    def add_subject_from_file(self, filename, subjectname=None, groupname=None):
        if subjectname is None:
            subjectname = self.define_subjectname_from_filename(filename)
        if groupname is None:
            groupname = Subject.DEFAULT_GROUP
        subject = Subject(groupname, subjectname, filename)
        self.add_subject(subject)
        
    @staticmethod
    def _create_analysis():
        raise NotImplementedError("Study is an abstract class.")
  
    @staticmethod
    def analysis_cls():
        raise NotImplementedError("Study is an abstract class")

    def set_analysis_parameters(self, parameter_template):
        for subject in self.subjects:
            self.analyses[subject.id()].set_parameters(parameter_template, subject,
                                                  self.outputdir)

    def import_data(self, parameter_template):
        subjects_failed = []
        for subject in self.subjects:
            try:
                new_imgname = self.analysis_cls().import_data(parameter_template, 
                                                              subject, self.outputdir)
                subject.filename = new_imgname
            except ImportationError:
                subjects_failed.append(subject) 
        if len(subjects_failed) > 0:
            for subject in subjects_failed:
                self.subjects.remove(subject)
                del self.analyses[subject.id()]
            raise ImportationError("The importation failed for the following subjects:\n%s."
                                   % ", ".join([str(subject) for subject in subjects_failed]))

    def has_subjects(self):
        return len(self.subjects) != 0

    def has_some_results(self):
        for analysis in self.analyses.itervalues():
            if analysis.outputs.some_file_exists():
                return True
        return False

    def has_all_results(self):
        for analysis in self.analyses.itervalues():
            if not analysis.outputs.all_file_exists():
                return False
        return True

    def clear_results(self):
        for analysis in self.analyses.itervalues():
            analysis.clear_output_files()

    def __repr__(self):
        s = 'name :' + str(self.name) + '\n'
        s += 'outputdir :' + str(self.outputdir) + '\n'
        s += 'subjects :' + repr(self.subjects) + '\n'
        return s


def remove_all_extensions(filename):
    name, ext = os.path.splitext(os.path.basename(filename))
    while (ext != ""):
        name, ext = os.path.splitext(name)
    return name


class StudySerializationError(Exception):
    pass

class SubjectExistsError(Exception):
    pass
