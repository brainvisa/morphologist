import unittest
import time
    
from morphologist.runner import ThreadRunner
from morphologist.tests.study import MockStudyTestCase#, BrainvisaStudyTestCase
    
class TestRunner(unittest.TestCase):
    
    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters() 
        self.study = self.test_case.study
        self.runner = self.create_runner(self.study)
    
    def create_runner(self, study):
        return ThreadRunner(study)
        #return SWRunner()
    
    def create_test_case(self):
        #test_case = BrainvisaStudyTestCase()
        test_case = MockStudyTestCase()
        return test_case

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
        
        self.assert_(self.runner.is_running())
        
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
        
        self.assert_output_files_cleared()
        
    def _test_missing_input_file_error(self):
        #TODO
        pass
    
    def _test_output_file_exist_error(self):
        #TODO
        pass
        
    def assert_output_files_exist(self):
        self.assertEqual(len(self.study.list_subjects_with_missing_results()), 0)
        
    def assert_output_files_cleared(self):
        self.assertEqual(len(self.study.list_subjects_with_some_results()), 0)
        
        
    def tearDown(self):
        if self.runner.is_running():
            self.runner.stop()
        
        
if __name__=='__main__':
    unittest.main()        