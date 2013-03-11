import sys
import time
import unittest
import optparse
    
from morphologist.core.runner import MissingInputFileError, \
    Runner, SomaWorkflowRunner, ThreadRunner
from morphologist.core.tests.study import MockStudyTestCase


class TestRunner(unittest.TestCase):
    
    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.study = self.test_case.study
        self.runner = self.create_runner(self.study)
    
    def create_runner(self, study):
        raise NotImplementedError("TestRunner is an abstract class.")
    
    def create_test_case(self):
        return MockStudyTestCase()
   
   
    def tearDown(self):
        if self.runner.is_running():
            self.runner.stop()
            
            
class TestRunnerOnSuccessStudy(TestRunner):
     
    def test_run_all_subjects(self):
        self.study.clear_results()
        self.runner.run()
        
        self.assert_(self.runner.is_running() or self.study.has_all_results())
        
    def test_run_selected_subjects(self):
        self.study.clear_results()
        selected_subject_id = self.test_case.get_a_subject_id()
        self.runner.run(subject_ids=[selected_subject_id])
        
        for subject_id in self.study.subjects:
            if subject_id == selected_subject_id:
                self.assert_(self.runner.is_running(subject_id) or \
                             self.study.has_all_results([subject_id]))
            else:
                self.assert_(not self.runner.is_running(subject_id))
        
    def test_has_run(self):
        self.study.clear_results()
        self.runner.run()
        self.runner.wait()
        
        self.assert_(not self.runner.is_running())
        self.assert_(not self.runner.has_failed())
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
       
        self.assert_output_files_exist_only_for_succeed_steps_after_stop()
 
    def test_clear_state_after_waiting_a_given_step_1(self):
        subject_id, stepname = self.test_case.step_to_wait_testcase_1()
        self._test_clear_state_after_waiting_a_given_step(subject_id, stepname)

    def test_clear_state_after_waiting_a_given_step_2(self):
        subject_id, stepname = self.test_case.step_to_wait_testcase_2()
        self._test_clear_state_after_waiting_a_given_step(subject_id, stepname)

    def test_clear_state_after_waiting_a_given_step_3(self):
        subject_id, stepname = self.test_case.step_to_wait_testcase_3()
        self._test_clear_state_after_waiting_a_given_step(subject_id, stepname)

    def _test_clear_state_after_waiting_a_given_step(self,
                                    subject_id, stepname):
        self.study.clear_results()
        self.runner.run()
        self.runner.wait(subject_id, stepname)
        if self.runner.is_running(): self.runner.stop()
        self.assert_output_files_exist_only_for_succeed_steps_after_stop()
 
    def test_missing_input_file_error(self):
        self.study.clear_results()
        self.test_case.delete_some_input_files()

        self.assertRaises(MissingInputFileError, self.runner.run)

    def assert_output_files_exist(self):
        self.assertTrue(self.study.has_all_results())
       
    def assert_output_files_cleared_or_all_exists(self):
        self.assertTrue((not self.study.has_some_results()) or
                        self.study.has_all_results())

    def assert_output_files_exist_only_for_succeed_steps_after_stop(self):
        step_status = self.runner.get_steps_status()
        for step_status_for_subject in step_status.itervalues():
            for (step, status) in step_status_for_subject.itervalues():
                if status == Runner.SUCCESS:
                    self.assertTrue(step.outputs.all_file_exists())
                elif status in Runner.KILLED_BY_USER:
                    self.assertTrue(not step.outputs.some_file_exists())
                else:
                    self.assertTrue(0)
        
    def tearDown(self):
        super(TestRunnerOnSuccessStudy, self).tearDown()
        #some input files are removed in test_missing_input_file_error:
        self.test_case.restore_input_files() 


class TestSomaWorkflowRunner(TestRunnerOnSuccessStudy):

    def create_runner(self, study):
        return SomaWorkflowRunner(study)


class TestThreadRunner(TestRunnerOnSuccessStudy):

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
