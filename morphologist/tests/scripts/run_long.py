import unittest

from morphologist.tests.test_steps import TestIntraAnalysisSteps


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)

    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(Test???))

    unittest.TextTestRunner(verbosity=2).run(suite)


