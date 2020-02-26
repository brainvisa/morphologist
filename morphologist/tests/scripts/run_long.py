from __future__ import absolute_import
import unittest

from morphologist.tests.intra_analysis.test_steps import TestIntraAnalysisSteps
from morphologist.tests.intra_analysis.test_runner import TestIntraAnalysisSomaWorkflowRunner


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSomaWorkflowRunner))

    unittest.TextTestRunner(verbosity=2).run(suite)


