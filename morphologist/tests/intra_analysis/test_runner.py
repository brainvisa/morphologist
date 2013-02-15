import unittest

from morphologist.core.tests.test_runner import TestSomaWorkflowRunner
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCase, IntraAnalysisStudyTestCaseBvParamTemplate 


class TestIntraAnalysisSomaWorkflowRunner(TestSomaWorkflowRunner):

    def create_test_case(self):
        return IntraAnalysisStudyTestCase()


class TestIntraAnalysisBvParamTemplateSomaWorkflowRunner(TestSomaWorkflowRunner):

    def create_test_case(self):
        return IntraAnalysisStudyTestCaseBvParamTemplate()


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisBvParamTemplateSomaWorkflowRunner)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSomaWorkflowRunner))
    unittest.TextTestRunner(verbosity=2).run(suite)

