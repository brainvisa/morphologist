import unittest

from morphologist.core.study import Study
from morphologist.core.tests.analysis import MockAnalysisTestCase
from capsul.pipeline import pipeline_tools

class MissingParameterValueError(Exception):
    pass

class UnknownParameterName(Exception):
    pass



class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case() 
        self.study = Study(analysis_type='MockAnalysis', study_name="none",
                           output_directory='/tmp')
        self.analysis = self.test_case.create_analysis(self.study)

    def create_test_case(self):
        test_case = MockAnalysisTestCase()
        return test_case

    def test_missing_parameter_value_error(self):
        self.test_case.set_analysis_parameters()
        self.test_case.delete_some_parameter_values()

        pipeline = self.analysis.pipeline.process
        pipeline.enable_all_pipeline_steps()
        pipeline_tools.disable_runtime_steps_with_existing_outputs(
            pipeline)

        missing = pipeline_tools.nodes_with_missing_inputs(pipeline)

        self.assertTrue(missing)

    def test_unknown_parameter_error(self):
        self.test_case.set_analysis_parameters()
        wrong_parameter_name = self.test_case.get_wrong_parameter_name()

        self.assertRaises(KeyError,
                          self.analysis.parameters['state'].__getitem__,
                          wrong_parameter_name)

    def test_clear_results(self):
        self.test_case.set_analysis_parameters()
        self.test_case.create_some_output_files()

        self.assertTrue(self.analysis.has_some_results())
        self.analysis.clear_results()
        self.assertTrue(not self.analysis.has_some_results())

    def test_step_id(self):
        self.assertEqual(len(self.analysis._step_ids),
                         len(self.analysis._steps))

    def tearDown(self):
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
