import unittest

from morphologist.tests.intra_analysis.test_steps import TestIntraAnalysisSteps
from morphologist.tests.intra_analysis.test_runner import TestRunnerIntraAnalysisSomaWorkflow

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerIntraAnalysisSomaWorkflow))

    unittest.TextTestRunner(verbosity=2).run(suite)


