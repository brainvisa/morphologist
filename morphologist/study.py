import os
import json

from morphologist.analysis import InputParameters, OutputParameters, ImportationError


class Subject(object):
    
    def __init__(self, imgname, groupname=None):
        self.imgname = imgname
        self.groupname = groupname

    def __repr__(self):
        s = '\timgname: ' + str(self.imgname) + ',\n'
        s += '\tgroupname: ' + str(self.groupname) + '\n'
        return s

    def serialize(self):
        serialized = {}
        serialized['imgname'] = self.imgname
        serialized['groupname'] = self.groupname
        return serialized

    @classmethod
    def unserialize(cls, serialized):
        subject = cls(imgname=serialized['imgname'], 
                      groupname=serialized['groupname'])
        return subject


class Study(object):
    DEFAULT_GROUP = "group1"
    default_outputdir = os.path.join(os.path.expanduser("~"),
                                'morphologist/studies/study')
    
    def __init__(self, name="undefined study",
        outputdir=default_outputdir, backup_filename=None):
        self.name = name
        self.outputdir = outputdir
        self.subjects = {}
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
        for subject_name, serialized_subject in serialized['subjects'].iteritems():
            study.subjects[subject_name] = Subject.unserialize(serialized_subject)
        for subject_name in study.subjects.iterkeys():
            if subject_name not in serialized['input_params']:
                raise StudySerializationError("Cannot find input params"
                                         " for subject %s" %subject_name)
            if subject_name not in serialized['output_params']:
                raise StudySerializationError("Cannot find output params" 
                                         " for subject %s" %subject_name)
            serialized_input_params = serialized['input_params'][subject_name] 
            serialized_output_params = serialized['output_params'][subject_name]
            input_params = InputParameters.unserialize(serialized_input_params) 
            output_params = OutputParameters.unserialize(serialized_output_params)
            analysis = cls._create_analysis()
            analysis.input_params = input_params
            analysis.output_params = output_params
            # TODO => check if the parameters are compatibles with the analysis ?
            study.analyses[subject_name] = analysis
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
        serialized['subjects'] = {}
        for subjectname, subject in self.subjects.iteritems():
            serialized['subjects'][subjectname] = subject.serialize()
        serialized['input_params'] = {}
        serialized['output_params'] = {}
        for subjectname, analysis in self.analyses.iteritems():
            serialized['input_params'][subjectname] = analysis.input_params.serialize()
            serialized['output_params'][subjectname] = analysis.output_params.serialize()
        return serialized 

    @staticmethod
    def define_subjectname_from_filename(filename):
        return remove_all_extensions(filename)

    def add_subject_from_file(self, filename, subjectname=None, groupname=None):
        if subjectname is None:
            subjectname = self.define_subjectname_from_filename(filename)
        if groupname is None:
            groupname = self.DEFAULT_GROUP
        if subjectname in self.subjects:
            raise SubjectNameExistsError(subjectname)
        subject = Subject(filename, groupname)
        self.subjects[subjectname] = subject
        self.analyses[subjectname] = self._create_analysis()

    @staticmethod
    def _create_analysis():
        raise Exception("Study is an abstract class.")
  
    @staticmethod
    def _analysis_cls():
        raise Exception("Study is an abstract class")

    def set_analysis_parameters(self, parameter_template):
        for subjectname, subject in self.subjects.iteritems():
            self.analyses[subjectname].set_parameters(parameter_template,
                                                      subject.groupname, 
                                                      subjectname,
                                                      subject.imgname,
                                                      self.outputdir)

    def import_data(self, parameter_template):
        subjects_failed = []
        for subjectname, subject in self.subjects.iteritems():
            try:
                new_imgname = self._analysis_cls().import_data(parameter_template, 
                                                                 subject.imgname,
                                                                 subject.groupname,
                                                                 subjectname,
                                                                 self.outputdir)
                subject.imgname = new_imgname
            except ImportationError:
                subjects_failed.append(subjectname) 
        if len(subjects_failed) > 0:
            for subjectname in subjects_failed:
                del self.subjects[subjectname]
                del self.analyses[subjectname]
            raise ImportationError("The importation failed for the following subjects:\n%s."
                                   % ", ".join(subjects_failed))

    def has_subjects(self):
        return len(self.subjects) != 0
                        
    def list_subject_names(self):
        return self.subjects.keys()

    def list_subjects_with_some_results(self):
        subjects = []
        for subjectname, analysis in self.analyses.iteritems():
            if analysis.list_existing_output_files():
                subjects.append(subjectname)
        return subjects
    
    def list_subjects_with_missing_results(self):
        subjects = []
        for subjectname, analysis in self.analyses.iteritems():
            if analysis.list_missing_output_files():
                subjects.append(subjectname)
        return subjects

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

class SubjectNameExistsError(Exception):
    pass
