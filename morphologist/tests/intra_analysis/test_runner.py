from __future__ import absolute_import
import unittest
import optparse
import sys

from morphologist.core.tests.test_runner import TestSomaWorkflowRunner
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCase, IntraAnalysisStudyTestCaseBvParamTemplate 


class TestIntraAnalysisSomaWorkflowRunner(TestSomaWorkflowRunner):

    def create_test_case(self):
        return IntraAnalysisStudyTestCase()


class TestIntraAnalysisBvParamTemplateSomaWorkflowRunner(TestSomaWorkflowRunner):

    def create_test_case(self):
        return IntraAnalysisStudyTestCaseBvParamTemplate()


if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test', 
                      dest="test", default=None, 
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisBvParamTemplateSomaWorkflowRunner)
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSomaWorkflowRunner))
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([TestIntraAnalysisBvParamTemplateSomaWorkflowRunner(options.test), 
                                         TestIntraAnalysisSomaWorkflowRunner(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)

