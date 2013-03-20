import unittest

from morphologist.tests.intra_analysis.test_runner_mock_analysis import TestMockIntraAnalysisSomaWorkflowRunner
from morphologist.core.tests.test_runner import TestSomaWorkflowRunner
from morphologist.core.tests.test_runner_on_failed_study import TestRunnerOnFailedStudy 
from morphologist.core.tests.test_object3d import TestObject3D


if __name__=='__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestMockIntraAnalysisSomaWorkflowRunner)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSomaWorkflowRunner))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerOnFailedStudy))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestObject3D))

    unittest.TextTestRunner(verbosity=2).run(suite)


