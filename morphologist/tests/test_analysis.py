import unittest
import os
import time

from morphologist.analysis import Analysis, InputParameters, OutputParameters
from morphologist.analysis import MockAnalysis
from morphologist.analysis import MissingParameterValueError, MissingInputFileError, OutputFileExistError, UnknownParameterName
 

class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case() 
        self.analysis = self.test_case.create_analysis()

    def create_test_case(self):
        test_case = MockAnalysisTestCase()
        return test_case

    def test_run_analysis(self):
        self.test_case.set_analysis_parameters()

        self.analysis.run()

        self.assert_(self.analysis.is_running())


    def test_analysis_has_run(self):
        self.test_case.set_analysis_parameters()
        self.analysis.run()

        self.analysis.wait()

        self.assert_(not self.analysis.last_run_failed())
        self.assert_output_files_exist()


    def test_stop_analysis(self):
        self.test_case.set_analysis_parameters()
        self.analysis.run()
        time.sleep(1) # tested analysis are longer to run than 1 second

        self.analysis.stop()

        self.assert_(not self.analysis.is_running())


    def test_clear_state_after_interruption(self):
        self.test_case.set_analysis_parameters()
        self.analysis.run()
        time.sleep(1) # tested analysis are longer to run than 1 second

        self.analysis.stop()

        self.assert_output_files_cleared()


    def test_missing_parameter_value_error(self):
        self.test_case.set_analysis_parameters()
        self.test_case.delete_some_parameter_values()

        self.assertRaises(MissingParameterValueError, Analysis.run, self.analysis)
        

    def test_missing_input_file_error(self):
        self.test_case.set_analysis_parameters()
        self.test_case.delete_some_input_files()

        self.assertRaises(MissingInputFileError, Analysis.run, self.analysis)


    def test_output_file_exist_error(self):
        self.test_case.set_analysis_parameters()
        self.test_case.create_some_output_files()

        self.assertRaises(OutputFileExistError, Analysis.run, self.analysis)

    def test_unknown_parameter_error(self):
        wrong_parameter_name = self.test_case.get_wrong_parameter_name()

        self.assertRaises(UnknownParameterName, 
                          InputParameters.get_value, 
                          self.analysis.input_params, wrong_parameter_name)


    def tearDown(self):
        if self.analysis.is_running():
            self.analysis.stop()
        self.test_case.restore_input_files()


    def assert_output_files_exist(self):
        for arg_name in self.analysis.output_params.list_file_parameter_names():
            out_file_path = self.analysis.output_params.get_value(arg_name)
            self.assert_(os.path.isfile(out_file_path))  


    def assert_output_files_cleared(self):
        for arg_name in self.analysis.output_params.list_file_parameter_names():
            out_file_path = self.analysis.output_params.get_value(arg_name)
            self.assert_(not os.path.isfile(out_file_path))  



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
