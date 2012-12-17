import unittest

from morphologist.tests.test_runner import TestRunnerSomaWorkflow, TestRunnerThread
from morphologist.tests.intra_analysis_study import IntraAnalysisStudyTestCase, IntraAnalysisStudyTestCaseBvParamTemplate 

class TestRunnerIntraAnalysisSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return IntraAnalysisStudyTestCase()

class TestRunnerIntraAnalysisBvParamTemplateSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return IntraAnalysisStudyTestCaseBvParamTemplate()

class TestRunnerIntraAnalysisThread(TestRunnerThread):

    def create_test_case(self):
        return IntraAnalysisStudyTestCase()

class TestRunnerIntraAnalysisBvParamTemplateThread(TestRunnerThread):

    def create_test_case(self):
        return IntraAnalysisStudyTestCaseBvParamTemplate()



if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisBvParamTemplateSomaWorkflow)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisSomaWorkflow))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisThread))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisBvParamTemplateThread))
    unittest.TextTestRunner(verbosity=2).run(suite)

