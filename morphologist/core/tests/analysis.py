import os

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

    def create_analysis(self):
        param_template = self.analysis_cls().create_default_parameter_template(self.output_directory)
        self.analysis = self.analysis_cls()(param_template)
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
        self.output_directory = os.path.join('/tmp', 'mock_analysis_test_case_output_directory')
        reset_directory(self.output_directory)

    def analysis_cls(self):
        return MockAnalysis

    def set_analysis_parameters(self):
        subject = Subject('foo', 'foo', os.path.join(self.output_directory, 'foo'))
        self.analysis.set_parameters(subject=subject)

    def delete_some_parameter_values(self):
        self.analysis.outputs.output_3 = None
        self.analysis.inputs.input_4 = None

    def create_some_output_files(self):
        parameter_names = ['output_1', 'output_4']
        for name in parameter_names:
            file_name = self.analysis.outputs.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def get_wrong_parameter_name(self):
        return "toto"


 
