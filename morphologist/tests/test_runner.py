import sys
import time
import unittest
import optparse
    
from morphologist.runner import MissingInputFileError, OutputFileExistError, \
    Runner, SomaWorkflowRunner, ThreadRunner
from morphologist.tests.study import MockStudyTestCase


class TestRunner(unittest.TestCase):
    
    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.study = self.test_case.study
        self.study.import_data(self.test_case.parameter_template())
        self.test_case.set_parameters() 
        self.runner = self.create_runner(self.study)
    
    def create_runner(self, study):
        raise NotImplementedError("TestRunner is an abstract class.")
    
    def create_test_case(self):
        return MockStudyTestCase()
    
    def test_run(self):
        self.study.clear_results()
        self.runner.run()
        
        self.assert_(self.runner.is_running() or 
                     (len(self.study.list_subjects_with_missing_results()) == 0))
        
    def test_has_run(self):
        self.study.clear_results()
        self.runner.run()
        self.runner.wait()
        
        self.assert_(not self.runner.is_running())
        self.assert_(not self.runner.last_run_failed())
        self.assert_output_files_exist()
        
    def test_stop(self):
        self.study.clear_results()
        self.runner.run()
        time.sleep(1)
        self.runner.stop()
    
        self.assert_(not self.runner.is_running())

    def test_clear_state_after_immediate_interruption(self):
        self.study.clear_results()
        self.runner.run()
        self.runner.stop()
       
        self.assert_output_files_exist_only_for_succeed_steps()
 
    def test_clear_state_after_waiting_a_given_step_1(self):
        self.study.clear_results()
        self.runner.run()
        analysis_name, stepname = self.test_case.step_to_wait_testcase_1()
        self.runner.wait_step(analysis_name, stepname)
        if self.runner.is_running(): self.runner.stop()
        self.assert_output_files_exist_only_for_succeed_steps()

    def test_clear_state_after_waiting_a_given_step_2(self):
        self.study.clear_results()
        self.runner.run()
        analysis_name, stepname = self.test_case.step_to_wait_testcase_2()
        self.runner.wait_step(analysis_name, stepname)
        if self.runner.is_running(): self.runner.stop()
        self.assert_output_files_exist_only_for_succeed_steps()
        
    def test_missing_input_file_error(self):
        self.study.clear_results()
        self.test_case.delete_some_input_files()

        self.assertRaises(MissingInputFileError, self.runner.run)

    def test_output_file_exist_error(self):
        self.study.clear_results()
        self.test_case.create_some_output_files()
        
        self.assertRaises(OutputFileExistError, self.runner.run)
       
    def assert_output_files_exist(self):
        self.assertEqual(len(self.study.list_subjects_with_missing_results()), 0)
       
    def assert_output_files_cleared_or_all_exists(self):
        self.assert_(len(self.study.list_subjects_with_some_results()) == 0 or 
                     len(self.study.list_subjects_with_missing_results()) == 0)

    def assert_output_files_exist_only_for_succeed_steps(self):
        step_status = self.runner.steps_status()
        for subjectname, step_status_for_subject in step_status.items():
            for stepname, (step, status) in step_status_for_subject.items():
                if status == Runner.SUCCESS:
                    self.assertTrue(len(step.outputs.list_missing_files()) == 0)
                elif status in [Runner.FAILED, Runner.NOT_STARTED]:
                    self.assertTrue(len(step.outputs.list_existing_files()) == 0)
                else:
                    self.assertTrue(0)
        
    def tearDown(self):
        if self.runner.is_running():
            self.runner.stop()
        #some input files are removed in test_missing_input_file_error:
        self.test_case.restore_input_files() 


class TestSomaWorkflowRunner(TestRunner):

    def create_runner(self, study):
        return SomaWorkflowRunner(study)


class TestThreadRunner(TestRunner):

    def create_runner(self, study):
        return ThreadRunner(study)


if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test', 
                      dest="test", default=None, 
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSomaWorkflowRunner)
        # XXX: commented because ThreadRunner does not work anymore
        #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestThreadRunner))
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([TestSomaWorkflowRunner(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
