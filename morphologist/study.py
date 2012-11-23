import os
import json

from morphologist.analysis import InputParameters, OutputParameters
from morphologist.intra_analysis import IntraAnalysis


class Subject(object):

    def __init__(self, imgname, groupname=None):
        self.imgname = imgname
        self.groupname = groupname

    def __repr__(self):
        s = '\t<imgname: ' + str(self.imgname) + ',\n'
        s += '\tgroupname: ' + str(self.groupname) + ',\n'
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
    default_outputdir = os.path.join(os.getcwd(), '.config/morphologist/studies/study')

    def __init__(self, name="undefined study", outputdir=default_outputdir):
        self.name = name
        self.outputdir = outputdir
        self.subjects = {}
        self.analysis = {}

    @classmethod
    def from_file(cls, file_path):
        try:
            with open(file_path, "r") as fd:
                    serialized_study = json.load(fd)
        except Exception, e:
            raise StudySerializationError("%s" %(e))

        try:
            study = cls.unserialize(serialized_study)
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
            # TO DO => check if the parameters are compatibles with the analysis ?
            study.analysis[subject_name] = analysis
        return study

    def save_to_file(self, filename):
        serialized_study = self.serialize()
        try:
            with open(filename, "w") as fd:
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
        for subjectname, analysis in self.analysis.iteritems():
            serialized['input_params'][subjectname] = analysis.input_params.serialize()
            serialized['output_params'][subjectname] = analysis.output_params.serialize()
        return serialized 


    @staticmethod
    def define_subjectname_from_filename(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def add_subject_from_file(self, filename, subjectname=None, groupname=None):
        if subjectname is None:
            subjectname = self.define_subjectname_from_filename(subjectname)
        if subjectname in self.subjects:
            raise SubjectNameExistsError(subjectname)
        subject = Subject(filename, groupname)
        self.subjects[subjectname] = subject
        self.analysis[subjectname] = self._create_analysis()

    @staticmethod
    def _create_analysis():
        return IntraAnalysis() 


    def set_analysis_parameters(self, parameter_template):
        for subjectname, subject in self.subjects.iteritems():
            self.analysis[subjectname].set_parameters(parameter_template, 
                                                      subjectname,
                                                      subject.imgname,
                                                      self.outputdir)
        
    def list_subject_names(self):
        return self.subjects.keys()

    def run_analyses(self):
        for analysis in self.analysis.itervalues():
            analysis.run()     

    def wait_analyses_end(self):
        for analysis in self.analysis.itervalues():
            analysis.wait()

    def stop_analyses(self):
        for analysis in self.analysis.itervalues():
            analysis.stop()

    def analyses_ended_with_success(self):
        success = True
        for analysis in self.analysis.itervalues():
            if analysis.last_run_failed():
                success = False
                break
        return success

    def clear_results(self):
        for analysis in self.analysis.itervalues():
            analysis.clear_output_files()

    def __repr__(self):
        s = 'name :' + str(self.name) + '\n'
        s += 'outputdir :' + str(self.outputdir) + '\n'
        s += 'subjects :' + repr(self.subjects) + '\n'
        return s


class StudySerializationError(Exception):
    pass

class SubjectNameExistsError(Exception):
    pass
