import os

from morphologist.tests.mocks.analysis import MockAnalysis
from morphologist.tests import remove_file, reset_directory

class AnalysisTestCase(object):
    ''' abstract class '''
    def __init__(self):
        self.analysis = None

    def analysis_cls(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def create_analysis(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def set_analysis_parameters(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def delete_some_parameter_values(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def create_some_output_files(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def get_wrong_parameter_name(self):
        raise Exception("AnalysisTestCase is an abstract class")


class MockAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(MockAnalysisTestCase, self).__init__()
        self.outputdir = os.path.join('/tmp', 'mock_analysis_test_case_outputdir')
        reset_directory(self.outputdir)

    def analysis_cls(self):
        return MockAnalysis

    def create_analysis(self):
        self.analysis = MockAnalysis()
        return self.analysis

    def set_analysis_parameters(self):
        self.analysis.set_parameters(parameter_template='foo', 
                                     name='foo',
                                     image='foo',
                                     outputdir=self.outputdir)

    def delete_some_parameter_values(self):
        self.analysis.output_params.output_3 = None
        self.analysis.input_params.input_4 = None

    def create_some_output_files(self):
        parameter_names = ['output_1', 'output_4']
        for name in parameter_names:
            file_name = self.analysis.output_params.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def get_wrong_parameter_name(self):
        return "toto"


 