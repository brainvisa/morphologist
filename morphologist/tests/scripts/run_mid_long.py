import unittest

from morphologist.tests.test_runner_mock_intra_analysis import TestRunnerMockIntraAnalysisThread, TestRunnerMockIntraAnalysisSomaWorkflow

if __name__=='__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisSomaWorkflow)
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisThread))

    unittest.TextTestRunner(verbosity=2).run(suite)


