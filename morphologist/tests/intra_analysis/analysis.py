import os
import getpass

from morphologist.core.study import Subject
from morphologist.intra_analysis import IntraAnalysis
from morphologist.core.tests.analysis import AnalysisTestCase
from morphologist.core.tests import reset_directory


class IntraAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(IntraAnalysisTestCase, self).__init__()
        self.outputdir = os.path.join('/neurospin', 'tmp', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(), 
                                      IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)
        reset_directory(self.outputdir)

    def create_analysis(self):
        self.analysis = IntraAnalysis()
        return self.analysis

    def analysis_cls(self):
        return IntraAnalysis

    def set_analysis_parameters(self):
        subjectname = "hyperion"
        groupname = "group1"
        
        filename = os.path.join('/neurospin', 'lnao', 'Panabase',
            'cati-dev-prod', 'morphologist', 'raw_irm', subjectname + ".nii")
         
        subject = Subject(subjectname, groupname, filename)
        self.analysis.set_parameters(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE,
                                     subject=subject, outputdir=self.outputdir) 
        IntraAnalysis.create_outputdirs(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE,
                                        subject, self.outputdir)
        self.analysis.clear_results() 

    def delete_some_parameter_values(self):
        self.analysis.outputs.edges = None
        self.analysis.inputs.mri = None

    def create_some_output_files(self):
        parameter_names = [IntraAnalysis.SPLIT_MASK, IntraAnalysis.HFILTERED]
        for name in parameter_names:
            file_name = self.analysis.outputs.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close() 

    def get_wrong_parameter_name(self):
        return "toto"



