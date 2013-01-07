import unittest

from morphologist.tests.intra_analysis.test_runner_mock_analysis import TestRunnerMockIntraAnalysisSomaWorkflow

if __name__=='__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisSomaWorkflow)

    unittest.TextTestRunner(verbosity=2).run(suite)


