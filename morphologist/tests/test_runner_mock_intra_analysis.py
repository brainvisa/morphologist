import unittest

from morphologist.tests.test_runner import TestRunnerSomaWorkflow, TestRunnerThread
from morphologist.tests.intra_analysis_study import MockIntraAnalysisStudyTestCase, MockIntraAnalysisStudyTestCaseBvParamTemplate

class TestRunnerMockIntraAnalysisSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCase() 

class TestRunnerMockIntraAnalysisBvParamTemplateSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCaseBvParamTemplate()

class TestRunnerMockIntraAnalysisThread(TestRunnerThread):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCase()

class TestRunnerMockIntraAnalysisBvParamTemplateThread(TestRunnerThread):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCaseBvParamTemplate()




if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisSomaWorkflow)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisBvParamTemplateSomaWorkflow))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisThread))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisiBvParamTemplateThread))
    unittest.TextTestRunner(verbosity=2).run(suite)
