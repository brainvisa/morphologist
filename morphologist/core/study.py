import os
import json

from morphologist.core.utils import OrderedDict, remove_all_extensions
from morphologist.core.analysis import Parameters, ImportationError
from morphologist.core.constants import ALL_SUBJECTS


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

    def copy(self):
        return Subject(self.name, self.groupname, self.filename)


class Study(object):
    default_outputdir = os.path.join(os.path.expanduser("~"),
                                'morphologist/studies/study')
    
    def __init__(self, name="undefined study", outputdir=default_outputdir,
                            backup_filename=None, parameter_template=None):
        self.name = name
        self.outputdir = outputdir
        self.subjects = OrderedDict()
        if parameter_template is None:
            parameter_template = self.analysis_cls().PARAMETER_TEMPLATES[0]
        self.parameter_template = parameter_template
        if backup_filename is None:
            backup_filename = self.default_backup_filename_from_outputdir(outputdir)
        self.backup_filename = backup_filename
        self.analyses = {}

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
        self.analyses[subject_id].set_parameters(self.parameter_template,
                                                subject, self.outputdir)
        try:
            new_imgname = self.analysis_cls().import_data(\
                                        self.parameter_template, 
                                        subject, self.outputdir)
        except ImportationError:
            del self.subjects[subject_id]
            del self.analyses[subject_id]
            raise ImportationError("Importation failed for the " +
                        "following subject: %s." % str(subject))
        else:
            subject.filename = new_imgname

    @staticmethod
    def _create_analysis():
        raise NotImplementedError("Study is an abstract class.")
  
    @staticmethod
    def analysis_cls():
        raise NotImplementedError("Study is an abstract class")

    def has_subjects(self):
        return len(self.subjects) != 0

    def has_some_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
            if analysis.has_some_results():
                return True
        return False

    def has_all_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
            if not analysis.has_all_results():
                return False
        return True

    def clear_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
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
