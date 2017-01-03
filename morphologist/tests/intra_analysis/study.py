import os
import getpass

from morphologist.core.tests.study import AbstractStudyTestCase
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames
from morphologist.core.tests import reset_directory


class IntraAnalysisStudyTestCase(AbstractStudyTestCase):
    '''    
    -> Intra analysis    
    -> Default parameter template
    '''

    def __init__(self):
        super(IntraAnalysisStudyTestCase, self).__init__()
        self.analysis_type = "IntraAnalysis"
        self.studyname = "study with param template: " + self.parameter_template_name() 
        test_dir = os.environ.get('BRAINVISA_TESTS_DIR')
        if not test_dir:
            raise RuntimeError('BRAINVISA_TESTS_DIR is not set')
        test_dir = os.path.join(test_dir, 'tmp_tests_brainvisa')
        self.output_directory = os.path.join(test_dir, 'morphologist-ui',
                                             self.parameter_template_name())
        inputdir = os.path.join(test_dir, 'data_unprocessed')
        basenames = ['sujet01.ima', 'sujet02.ima', 'sujet03.ima']
        self.subjectnames = [filename.split('.')[0] for filename in basenames]
        self.filenames = [os.path.join(inputdir, subject, 'anatomy', filename)
                          for filename, subject
                          in zip(basenames, self.subjectnames)]
        self.groupnames = ['group 1', 'group 2', 'group 3']

        reset_directory(self.output_directory)

    def parameter_template_name(self):
        return 'default'

    def delete_some_input_files(self):
        parameter_names = [IntraAnalysisParameterNames.MRI]
        for name in parameter_names:
            file_name = self.study.analyses.values()[1].inputs.get_value(name)
            os.rename(file_name, file_name + "hide_for_test") 

    def create_some_output_files(self):
        parameter_names = [IntraAnalysisParameterNames.SPLIT_MASK, 
                           IntraAnalysisParameterNames.VARIANCE]
        for name in parameter_names:
            file_name = getattr(
                self.study.analyses.values()[0].pipeline, name)
            try:
                os.makedirs(os.path.dirname(file_name))
            except OSError:
                pass
            f = open(file_name, "w")
            f.write("something\n")
            f.close() 

    def restore_input_files(self):
        parameter_names = [IntraAnalysisParameterNames.MRI]
        for name in parameter_names:
            file_name = getattr(
                self.study.analyses.values()[1].pippeline, name)
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

    def __init__(self):
        super(MockIntraAnalysisStudyTestCase, self).__init__()
        self.analysis_type = "MockIntraAnalysis"


class IntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):
    '''
    -> Intra analysis
    -> Brainvisa parameter template
    '''

    def parameter_template_name(self):
        return 'brainvisa'


class MockIntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):
    '''
    -> Brainvisa parameter template
    -> Mock intra analysis
    '''

    def __init__(self):
        super(MockIntraAnalysisStudyTestCaseBvParamTemplate, self).__init__()
        self.analysis_type = "MockIntraAnalysis"

    def parameter_template_name(self):
        return 'brainvisa'
