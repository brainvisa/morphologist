import unittest
import os
import time

from morphologist.analysis import MockStepFlow, Analysis, InputArguments, OutputArguments
from morphologist.analysis import MissingParameterValueError, MissingInputFileError, OutputFileExistError, UnknownParameterName
 

class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_case = create_test_case() 
        self.analysis = self.test_case.create_analysis()


    def test_run_analysis(self):
        self.test_case.set_analysis_parameters()

        self.analysis.run()

        self.assert_(self.analysis.is_running())


    def test_analysis_has_run(self):
        self.test_case.set_analysis_parameters()
        self.analysis.run()

        self.analysis.wait()

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
                          InputArguments.get_value, 
                          self.analysis.input_args, wrong_parameter_name)


    def tearDown(self):
        if self.analysis.is_running():
            self.analysis.stop()


    def assert_output_files_exist(self):
        for arg_name in self.analysis.output_args.list_file_argument_names():
            out_file_path = self.analysis.output_args.get_value(arg_name)
            self.assert_(os.path.isfile(out_file_path))  


    def assert_output_files_cleared(self):
        for arg_name in self.analysis.output_args.list_file_argument_names():
            out_file_path = self.analysis.output_args.get_value(arg_name)
            self.assert_(not os.path.isfile(out_file_path))  




def create_test_case():
    test_case = MockAnalysisTestCase()
    return test_case


class MockAnalysisTestCase(object):

    def __init__(self):
        self.analysis = None

    def create_analysis(self):
        mock_step_flow = MockStepFlow()
        self.analysis = Analysis(mock_step_flow)
        return self.analysis

    def set_analysis_parameters(self):
        self.analysis.input_args.input_1 = generate_in_file_path("input_1")
        self.analysis.input_args.input_2 = generate_in_file_path("input_2")
        self.analysis.input_args.input_3 = generate_in_file_path("input_3")
        self.analysis.input_args.input_4 = generate_in_file_path("input_4")
        self.analysis.input_args.input_5 = generate_in_file_path("input_5")
        self.analysis.input_args.input_6 = generate_in_file_path("input_6")

        self.analysis.output_args.output_1 = generate_out_file_path("output_1")
        self.analysis.output_args.output_2 = generate_out_file_path("output_2")
        self.analysis.output_args.output_3 = generate_out_file_path("output_3")
        self.analysis.output_args.output_4 = generate_out_file_path("output_4")
        self.analysis.output_args.output_5 = generate_out_file_path("output_5")
        self.analysis.output_args.output_6 = generate_out_file_path("output_6")

    def delete_some_parameter_values(self):
        self.analysis.output_args.output_3 = None
        self.analysis.input_args.input_4 = None

    def delete_some_input_files(self):
        parameter_names = ['input_2', 'input_5']
        for name in parameter_names:
            file_name = self.analysis.input_args.get_value(name)
            remove_file(file_name)

    def create_some_output_files(self):
        parameter_names = ['output_1', 'output_4']
        for name in parameter_names:
            file_name = self.analysis.output_args.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def get_wrong_parameter_name(self):
        return "toto"


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
