import os
import json

from morphologist.core.utils import OrderedDict, remove_all_extensions
from morphologist.core.analysis import Parameters, ImportationError


class Subject(object):
    DEFAULT_GROUP = "group1"
    
    def __init__(self, name, groupname, filename):
        self.name = name 
        self.groupname = groupname
        self.filename = filename

    @classmethod
    def from_filename(cls, filename, groupname=DEFAULT_GROUP):
        subjectname = cls._define_subjectname_from_filename(filename)
        return cls(subjectname, groupname, filename)

    @staticmethod
    def _define_subjectname_from_filename(filename):
        return remove_all_extensions(filename)
 
    def id(self):
        return self.groupname + "-" + self.name
        
    def __repr__(self):
        s = "(%s, %s, %s)" % (self.groupname, self.name, self.filename)
        return s

    def __str__(self):
        return self.id()
    
    def __cmp__(self, other):
        return cmp(self.id(), other.id())

    def serialize(self):
        serialized = {}
        serialized['subjectname'] = self.name
        serialized['groupname'] = self.groupname
        serialized['filename'] = self.filename
        return serialized

    @classmethod
    def unserialize(cls, serialized):
        subject = cls(name=serialized['subjectname'], 
                      groupname=serialized['groupname'],
                      filename=serialized['filename'])
        return subject


class Study(object):
    default_outputdir = os.path.join(os.path.expanduser("~"),
                                'morphologist/studies/study')
    
    def __init__(self, name="undefined study",
        outputdir=default_outputdir, backup_filename=None):
        self.name = name
        self.outputdir = outputdir
        self.subjects = OrderedDict()
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
            subject = Subject.unserialize(serialized_subject)
            study.subjects[subject.id()] = subject
        for subject_id, subject in study.subjects.iteritems():
            if subject_id not in serialized['inputs']:
                raise StudySerializationError("Cannot find input params"
                                         " for subject %s" % str(subject))
            if subject_id not in serialized['outputs']:
                raise StudySerializationError("Cannot find output params" 
                                         " for subject %s" % str(subject))
            serialized_inputs = serialized['inputs'][subject_id] 
            serialized_outputs = serialized['outputs'][subject_id]
            inputs = Parameters.unserialize(serialized_inputs) 
            outputs = Parameters.unserialize(serialized_outputs)
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
        for subject_id, subject in self.subjects.iteritems():
            serialized['subjects'].append(subject.serialize())
        serialized['inputs'] = {}
        serialized['outputs'] = {}
        for subject_id, analysis in self.analyses.iteritems():
            serialized['inputs'][subject_id] = analysis.inputs.serialize()
            serialized['outputs'][subject_id] = analysis.outputs.serialize()
        return serialized 

    def add_subject(self, subject):
        subject_id = subject.id()
        if subject_id in self.subjects:
            raise SubjectExistsError(subject)
        self.subjects[subject_id] = subject
        self.analyses[subject_id] = self._create_analysis()

    @staticmethod
    def _create_analysis():
        raise NotImplementedError("Study is an abstract class.")
  
    @staticmethod
    def analysis_cls():
        raise NotImplementedError("Study is an abstract class")

    def set_analysis_parameters(self, parameter_template):
        for subject_id, subject in self.subjects.iteritems():
            self.analyses[subject_id].set_parameters(parameter_template,
                                                subject, self.outputdir)

    def import_data(self, parameter_template):
        subjects_id_importation_failed = []
        for subject_id, subject in self.subjects.iteritems():
            try:
                new_imgname = self.analysis_cls().import_data(parameter_template, 
                                                              subject, self.outputdir)
                subject.filename = new_imgname
            except ImportationError:
                subjects_id_importation_failed.append(subject_id) 
        if len(subjects_id_importation_failed) > 0:
            repr_subjects = []
            for subject_id in subjects_id_importation_failed:
                repr_subjects.append(str(self.subjects[subject_id]))
                del self.subjects[subject_id]
                del self.analyses[subject_id]
            raise ImportationError("The importation failed for the " +
                    "following subjects:\n%s." % ", ".join(repr_subjects))

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
            analysis.clear_results()

    def __repr__(self):
        s = 'name :' + str(self.name) + '\n'
        s += 'outputdir :' + str(self.outputdir) + '\n'
        s += 'subjects :' + repr(self.subjects) + '\n'
        return s


class StudySerializationError(Exception):
    pass

class SubjectExistsError(Exception):
    pass
