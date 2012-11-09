from collections import defaultdict
import os

from morphologist.analysis import Analysis
from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis import IntraAnalysisInputParameters, IntraAnalysisOutputParameters


class Subject(object):

    def __init__(self, imgname, subjectname, groupname=None):
        self.imgname = imgname
        self.groupname = groupname

    def __repr__(self):
        s = '\t<imgname: ' + str(self.imgname) + ',\n'
        s += '\tgroupname: ' + str(self.groupname) + ',\n'
        return s


class Study(object):
    default_outputdir = os.path.join(os.getcwd(), '.morphologist/studies/study')

    def __init__(self, name="undefined study", outputdir=default_outputdir):
        self.name = name
        self.outputdir = outputdir
        self.subjects = {}
        self.analysis = {}

    @classmethod
    def define_subjectname_from_filename(self, filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def add_subject_from_file(self, filename, subjectname=None, groupname=None):
        if subjectname is None:
            subjectname = self.define_subjectname_from_filename(subjectname)
        if subjectname in self.subjects:
            raise SubjectNameExistsError("subjectname")
        subject = Subject(filename, subjectname, groupname)
        self.subjects[subjectname] = subject
        self.analysis[subjectname] = create_analysis()
        self.analysis[subjectname].input_params = create_input_parameters(subjectname,
                                                                          subject.imgname, 
                                                                          self.outputdir)
        self.analysis[subjectname].output_params = create_output_parameters(subjectname,
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



class SubjectNameExistsError(Exception):
    pass


def create_input_parameters(subject_name, img_file_path, output_dir):
    input_params = IntraAnalysisInputParameters.from_brainvisa_hierarchy(img_file_path)
    return input_params


def create_output_parameters(subject_name, img_file_path, output_dir):
    output_params = IntraAnalysisOutputParameters.from_brainvisa_hierarchy(output_dir, 
                                                                           subject_name)
    return output_params


def create_analysis():
    intra_analysis = IntraAnalysis()    
    return intra_analysis


