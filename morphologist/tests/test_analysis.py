import unittest
import os

from morphologist.analysis import Analysis, InputParameters 
from morphologist.analysis import MissingParameterValueError, UnknownParameterName
from morphologist.tests.mocks.analysis import MockAnalysis


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case() 
        self.analysis = self.test_case.create_analysis()

    def create_test_case(self):
        test_case = MockAnalysisTestCase()
        return test_case


    def test_missing_parameter_value_error(self):
        self.test_case.set_analysis_parameters()
        self.test_case.delete_some_parameter_values()

        self.assertRaises(MissingParameterValueError, Analysis.get_command_list, self.analysis)
        

    def test_unknown_parameter_error(self):
        wrong_parameter_name = self.test_case.get_wrong_parameter_name()

        self.assertRaises(UnknownParameterName, 
                          InputParameters.get_value, 
                          self.analysis.input_params, wrong_parameter_name)

    def test_clear_output_files(self):
        self.test_case.set_analysis_parameters()
        self.test_case.create_some_output_files()
        
        self.assertNotEqual(len(self.analysis.list_existing_output_files()), 0)
        self.analysis.clear_output_files()
        self.assertEqual(len(self.analysis.list_existing_output_files()), 0)
        
        
    def tearDown(self):
        pass


class AnalysisTestCase(object):
    ''' abstract class '''
    def __init__(self):
        self.analysis = None

    def create_analysis(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def set_analysis_parameters(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def delete_some_parameter_values(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def delete_some_input_files(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def create_some_output_files(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def get_wrong_parameter_name(self):
        raise Exception("AnalysisTestCase is an abstract class")

    def restore_input_files(self):
        raise Exception("AnalysisTestCase is an abstract class")

class MockAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(MockAnalysisTestCase, self).__init__()

    def create_analysis(self):
        self.analysis = MockAnalysis()
        return self.analysis

    def set_analysis_parameters(self):
        self.analysis.set_parameters(parameter_template='foo', 
                                     name='foo',
                                     image='foo',
                                     outputdir='/tmp')
 
    def delete_some_parameter_values(self):
        self.analysis.output_params.output_3 = None
        self.analysis.input_params.input_4 = None

    def delete_some_input_files(self):
        parameter_names = ['input_2', 'input_5']
        for name in parameter_names:
            file_name = self.analysis.input_params.get_value(name)
            remove_file(file_name)

    def create_some_output_files(self):
        parameter_names = ['output_1', 'output_4']
        for name in parameter_names:
            file_name = self.analysis.output_params.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def get_wrong_parameter_name(self):
        return "toto"

    def restore_input_files(self):
        # useless because the input files are created in set_analysis_parameters
        pass


def remove_file(file_name):
    if os.path.isfile(file_name):
        os.remove(file_name)


def generate_in_file_path(file_name):
    file_path = generate_file_path(file_name)
    f = open(file_path, "w")
    f.close()
    return file_path

def generate_out_file_path(file_name):
    file_path = generate_file_path(file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)
    return file_path

def generate_file_path(file_name):
    base_directory = "/tmp/"
    return os.path.join(base_directory, "analysis_test_" + file_name)
 
       



if __name__ == '__main__':
    
    unittest.main()
