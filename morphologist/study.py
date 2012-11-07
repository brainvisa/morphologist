from collections import defaultdict
import os

from morphologist.analysis import Analysis
from morphologist.intra_analysis import IntraAnalysisStepFlow
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
        self.analysis[subjectname] = create_analysis(subjectname,
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

def create_analysis(subject_name, img_file_path, output_dir):
    intra_analysis_step_flow = IntraAnalysisStepFlow()
   

    input_params = create_intra_analysis_input_parameters(subject_name,
                                                          img_file_path,
                                                          output_dir)
 
    output_params = create_intra_analysis_output_parameters(subject_name,
                                                            output_dir)

    intra_analysis_step_flow.input_params = input_params
    intra_analysis_step_flow.output_params = output_params
    intra_analysis = Analysis(intra_analysis_step_flow)    
    return intra_analysis


def create_intra_analysis_input_parameters(subject_name, 
                                           img_file_path, 
                                           output_dir):
    parameters = IntraAnalysisInputParameters()

    base_directory = os.path.join(output_dir, subject_name, "t1mri", "default_acquisition")
    
    parameters.mri = img_file_path
    parameters.commissure_coordinates = os.path.join(base_directory, 
                                                                  "%s.APC" % subject_name)
    parameters.erosion_size = 1.8
    parameters.bary_factor = 0.6

    return parameters

def create_intra_analysis_output_parameters(subject_name, output_dir):
    parameters = IntraAnalysisOutputParameters()
     
    base_directory = os.path.join(output_dir, subject_name, "t1mri", "default_acquisition")
    
    default_analysis_directory = os.path.join(base_directory, "default_analysis") 
    if not os.path.isdir(default_analysis_directory):
        os.mkdir(default_analysis_directory)
      
    segmentation_directory = os.path.join(default_analysis_directory, "segmentation")
    if not os.path.isdir(segmentation_directory):
        os.mkdir(segmentation_directory)

    parameters.hfiltered = os.path.join(default_analysis_directory, 
                                        "hfiltered_%s.ima" % subject_name)
    parameters.white_ridges = os.path.join(default_analysis_directory, 
                                           "whiteridge_%s.ima" % subject_name)
    parameters.edges = os.path.join(default_analysis_directory, 
                                    "edges_%s.ima" % subject_name)
    parameters.mri_corrected = os.path.join(default_analysis_directory, 
                             "nobias_%s.ima" % subject_name)
    parameters.variance = os.path.join(default_analysis_directory, 
                        "variance_%s.ima" % subject_name)
    parameters.histo_analysis = os.path.join(default_analysis_directory, 
                              "nobias_%s.han" % subject_name)
    parameters.brain_mask = os.path.join(segmentation_directory, 
                          "brain_%s.ima" % subject_name)
    parameters.split_mask = os.path.join(segmentation_directory, 
                          "voronoi_%s.ima" % subject_name)

    return parameters 
        
  
