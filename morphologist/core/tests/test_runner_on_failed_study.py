import unittest

from morphologist.core.tests.study import MockFailedStudyTestCase
from morphologist.core.runner import SomaWorkflowRunner
from morphologist.core.tests.test_runner import TestRunner


class TestRunnerOnFailedStudy(TestRunner):
     
    def create_runner(self, study):
        return SomaWorkflowRunner(study)
    
    def create_test_case(self):
        return MockFailedStudyTestCase()
    
    def test_has_failed(self):
        self.runner.run()
        self.runner.wait()
        
        self.assert_(self.runner.has_failed(update_status=False))
        
    def test_subject_has_failed(self):
        self.runner.run()
        self.runner.wait()
        subject_id = self.test_case.get_a_subject_id()
        
        self.assert_(self.runner.has_failed(subject_id))
        
    def test_failed_step(self):
        self.runner.run()
        self.runner.wait()
        subject_id = self.test_case.get_a_subject_id()
        
        step_ids = self.runner.get_failed_step_ids(subject_id)
        
        self.assert_(len(step_ids) == 1)
        self.assert_(step_ids[0] == self.test_case.failed_step_id)
        
        
if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerOnFailedStudy)
    unittest.TextTestRunner(verbosity=2).run(suite)