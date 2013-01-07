import unittest

from morphologist.tests.test_intra_analysis_steps import TestIntraAnalysisSteps
from morphologist.tests.test_runner_intra_analysis import TestRunnerIntraAnalysisSomaWorkflow

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisSomaWorkflow))

    unittest.TextTestRunner(verbosity=2).run(suite)


