import unittest

from morphologist.analysis import InputParameters 
from morphologist.analysis import MissingParameterValueError, UnknownParameterName
from morphologist.tests.analysis import MockAnalysisTestCase

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

        self.assertRaises(MissingParameterValueError, 
                          self.test_case.analysis_cls().get_command_list, 
                          self.analysis)

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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
