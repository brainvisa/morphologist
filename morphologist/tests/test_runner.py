import unittest
import time
    
from morphologist.runner import MissingInputFileError, OutputFileExistError, SomaWorkflowRunner, ThreadRunner
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
        raise Exception("TestRunner is an abstract class.")
    
    def create_test_case(self):
        return MockStudyTestCase()

#        ######
#        self.study.clear_results()
#        exporter = MyExporter(study)
#        exporter.export(file_name, subject_list, step_interval)
#        
#        ###########
#        runner = MyRunner(study) # thread, SW ...
#        runner.run(subject_list, step_interval)
#        runner.wait()
#        #runner.stop()
#        #runner.is_running()
#        runner.is_running(subject, step)
#        runner.ended_with_sucess(subject, step)
#        log = runner.execution_log()
#        log_subject = runner.execution_log(subject)
#        log_subject_step = runner.execution_log(subject, step)
#        
#        self.assert_(runner.ended_with_success())

    
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
    
    def test_clear_state_after_interruption(self):
        self.study.clear_results()
        self.runner.run()
        time.sleep(1)
        self.runner.stop()
       
        self.assert_output_files_cleared_or_all_exists()
        
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
        
    def tearDown(self):
        if self.runner.is_running():
            self.runner.stop()
        #some input files are removed in test_missing_input_file_error:
        self.test_case.restore_input_files() 


class TestRunnerSomaWorkflow(TestRunner):

  def create_runner(self, study):
      return SomaWorkflowRunner(study)


class TestRunnerThread(TestRunner):

    def create_runner(self, study):
        return ThreadRunner(study)
    

        
        
if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerSomaWorkflow)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerThread))
    unittest.TextTestRunner(verbosity=2).run(suite)