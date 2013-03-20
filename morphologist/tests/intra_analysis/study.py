import os
import getpass

from morphologist.intra_analysis.study import IntraAnalysisStudy
from morphologist.core.tests.study import AbstractStudyTestCase
from morphologist.intra_analysis import IntraAnalysis
from morphologist.tests.intra_analysis.mocks.study import MockIntraAnalysisStudy
from morphologist.core.tests import reset_directory


class IntraAnalysisStudyTestCase(AbstractStudyTestCase):
    '''    
    -> Intra analysis    
    -> Default parameter template
    '''

    def __init__(self):
        super(IntraAnalysisStudyTestCase, self).__init__()
        self.studyname = "study with param template: " + self.parameter_template() 
        self.outputdir = os.path.join('/neurospin', 'tmp',  
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(), 
                                      self.parameter_template())
        inputdir = os.path.join('/neurospin', 'lnao', 'Panabase', 
                                'cati-dev-prod', 'morphologist', 'raw_irm')
        basenames = ['caca.ima', 'chaos.nii.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(inputdir, filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']
        
        reset_directory(self.outputdir)

    def study_cls(self):
        return IntraAnalysisStudy

    def parameter_template(self):
        return IntraAnalysis.DEFAULT_PARAM_TEMPLATE 

    def delete_some_input_files(self):
        parameter_names = [IntraAnalysis.MRI]
        for name in parameter_names:
            file_name = self.study.analyses.values()[1].inputs.get_value(name)
            os.rename(file_name, file_name + "hide_for_test") 

    def create_some_output_files(self):
        parameter_names = [IntraAnalysis.SPLIT_MASK, IntraAnalysis.VARIANCE]
        for name in parameter_names:
            file_name = self.study.analyses.values()[0].outputs.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close() 

    def restore_input_files(self):
        parameter_names = [IntraAnalysis.MRI]
        for name in parameter_names:
            file_name = self.study.analyses.values()[1].inputs.get_value(name)
            if file_name != None and os.path.isfile(file_name + "hide_for_test"):
                os.rename(file_name + "hide_for_test", file_name) 

    def step_to_wait_testcase_1(self):
        subject_id = self.get_a_subject_id()
        return subject_id, '0_normalization'

    def step_to_wait_testcase_2(self):
        subject_id = self.get_a_subject_id()
        return subject_id, '2_histogram_analysis'

    def step_to_wait_testcase_3(self):
        subject_id = self.get_a_subject_id()
        return subject_id, '13_sulci'


class MockIntraAnalysisStudyTestCase(IntraAnalysisStudyTestCase):
    '''
    -> Mock intra analysis
    -> Default parameter template
    '''

    def study_cls(self):
        return MockIntraAnalysisStudy


class IntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):
    '''
    -> Intra analysis
    -> Brainvisa parameter template
    '''

    def parameter_template(self):
        return IntraAnalysis.BRAINVISA_PARAM_TEMPLATE 


class MockIntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):
    '''
    -> Brainvisa parameter template
    -> Mock intra analysis
    '''

    def study_cls(self):
        return MockIntraAnalysisStudy

    def parameter_template(self):
        return IntraAnalysis.BRAINVISA_PARAM_TEMPLATE 
