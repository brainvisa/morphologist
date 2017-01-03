import os
import traits.api as traits

from morphologist.core.subject import Subject
from morphologist.core.tests.mocks.analysis import MockAnalysis
from morphologist.core.tests import reset_directory


class AnalysisTestCase(object):
    ''' abstract class '''
    def __init__(self):
        self.analysis = None
        self.output_directory = None

    def analysis_cls(self):
        raise NotImplementedError("AnalysisTestCase is an abstract class")

    def create_analysis(self, study):
        self.analysis = self.analysis_cls()(study)
        return self.analysis

    def set_analysis_parameters(self):
        raise NotImplementedError("AnalysisTestCase is an abstract class")

    def delete_some_parameter_values(self):
        raise NotImplementedError("AnalysisTestCase is an abstract class")

    def create_some_output_files(self):
        raise NotImplementedError("AnalysisTestCase is an abstract class")

    def get_wrong_parameter_name(self):
        raise NotImplementedError("AnalysisTestCase is an abstract class")


class MockAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(MockAnalysisTestCase, self).__init__()
        test_dir = os.environ.get('BRAINVISA_TESTS_DIR')
        if not test_dir:
            raise RuntimeError('BRAINVISA_TESTS_DIR is not set')
        self.output_directory = os.path.join(
            test_dir,
            'tmp_tests_brainvisa/morphologist-ui/'
            'mock_analysis_test_case_output_directory')

        reset_directory(self.output_directory)

    def analysis_cls(self):
        return MockAnalysis

    def set_analysis_parameters(self):
        subject = Subject('foo', 'foo', os.path.join(self.output_directory,
                                                     'foo'))
        self.analysis.set_parameters(subject=subject)

    def delete_some_parameter_values(self):
        self.analysis.pipeline.process.output_image = traits.Undefined
        self.analysis.pipeline.process.other_output = traits.Undefined

    def create_some_output_files(self):
        parameter_names = ['output_image', 'output_image']
        for name in parameter_names:
            file_name = getattr(self.analysis.pipeline.process, name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def get_wrong_parameter_name(self):
        return "toto"


 
