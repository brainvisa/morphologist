import unittest

from morphologist.tests.test_runner import TestRunnerSomaWorkflow, TestRunnerThread
from morphologist.tests.intra_analysis_study import MockIntraAnalysisStudyTestCase

class TestRunnerMockIntraAnalysisSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCase() 

class TestRunnerMockIntraAnalysisThread(TestRunnerThread):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCase()


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisSomaWorkflow)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisThread))
    unittest.TextTestRunner(verbosity=2).run(suite)
