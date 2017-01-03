import os
import getpass

from morphologist.core.subject import Subject
from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames
from morphologist.core.tests.analysis import AnalysisTestCase
from morphologist.core.tests import reset_directory
# CAPSUL
from capsul.pipeline import pipeline_tools
import traits.api as traits


class IntraAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(IntraAnalysisTestCase, self).__init__()
        test_dir = os.environ.get('BRAINVISA_TESTS_DIR')
        if not test_dir:
            raise RuntimeError('BRAINVISA_TESTS_DIR is not set')
        test_dir = os.path.join(test_dir, 'tmp_tests_brainvisa')
        self.output_directory = os.path.join(test_dir, 'morphologist-ui',
                                             'brainvisa')
        reset_directory(self.output_directory)

    def analysis_cls(self):
        return IntraAnalysis

    def set_analysis_parameters(self):
        subjectname = "sujet02"
        groupname = "group1"
        
        test_dir = os.environ.get('BRAINVISA_TESTS_DIR')
        if not test_dir:
            raise RuntimeError('BRAINVISA_TESTS_DIR is not set')
        test_dir = os.path.join(test_dir, 'tmp_tests_brainvisa')

        filename = os.path.join(test_dir, 'data_unprocessed', subjectname,
                                'anatomy', subjectname + ".ima")
         
        subject = Subject(subjectname, groupname, filename)
        self.analysis.set_parameters(subject=subject) 

        from capsul.process import get_process_instance
        import_step = get_process_instance(
            'morphologist.capsul.import_t1_mri.ImportT1Mri')

        import_step.input = subject.filename
        import_step.output \
            = self.analysis.pipeline.process.t1mri
        import_step.referential = self.analysis.pipeline.process. \
            PrepareSubject_TalairachFromNormalization_source_referential
        pipeline_tools.create_output_directories(import_step)

        self.analysis.clear_results() 

    def delete_some_parameter_values(self):
        self.analysis.pipeline.process.edges = None
        self.analysis.pipeline.process.t1mri = traits.Undefined

    def create_some_output_files(self):
        parameter_names = [IntraAnalysisParameterNames.SPLIT_MASK, 
                           IntraAnalysisParameterNames.HFILTERED]
        for name in parameter_names:
            file_name = getattr(self.analysis.pipeline.process, name)
            dirname = os.path.dirname(file_name)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            f = open(file_name, "w")
            f.write("something\n")
            f.close() 

    def get_wrong_parameter_name(self):
        return "toto"



