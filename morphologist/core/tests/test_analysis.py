import unittest

from morphologist.core.analysis import Parameters 
from morphologist.core.analysis import MissingParameterValueError, UnknownParameterName
from morphologist.core.tests.analysis import MockAnalysisTestCase


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
                          Parameters.get_value, 
                          self.analysis.inputs, wrong_parameter_name)

    def test_clear_results(self):
        self.test_case.set_analysis_parameters()
        self.test_case.create_some_output_files()
        
        self.assertTrue(self.analysis.outputs.some_file_exists())
        self.analysis.clear_results()
        self.assertTrue(not self.analysis.outputs.some_file_exists())

    def test_step_id(self):
        self.assertEqual(len(self.analysis._named_steps),
                         len(self.analysis._steps))
        
    def tearDown(self):
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
