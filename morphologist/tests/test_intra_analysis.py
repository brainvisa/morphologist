import unittest
import os

from morphologist.tests.test_analysis import TestAnalysis
from morphologist.tests.intra_analysis import IntraAnalysisTestCase

class TestIntraAnalysis(TestAnalysis):

    def create_test_case(self):
        test_case = IntraAnalysisTestCase()
        return test_case



if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
