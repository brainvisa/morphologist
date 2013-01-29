import unittest

from morphologist.tests.intra_analysis.test_runner_mock_analysis import TestMockIntraAnalysisSomaWorkflowRunner
from morphologist.tests.test_object3d import TestObject3D

if __name__=='__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestMockIntraAnalysisSomaWorkflowRunner)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestObject3D))

    unittest.TextTestRunner(verbosity=2).run(suite)


