from __future__ import absolute_import
import sys
import optparse
import unittest

from morphologist.core.tests.test_runner import TestSomaWorkflowRunner
from morphologist.tests.intra_analysis.study import MockIntraAnalysisStudyTestCase, MockIntraAnalysisStudyTestCaseBvParamTemplate


#class TestMockIntraAnalysisSomaWorkflowRunner(TestSomaWorkflowRunner):

    #def create_test_case(self):
        #return MockIntraAnalysisStudyTestCase()


class TestMockIntraAnalysisBvParamTemplateSomaWorkflowRunner(
        TestSomaWorkflowRunner):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCaseBvParamTemplate()


if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test',
                      dest="test", default=None,
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        #suite = unittest.TestLoader().loadTestsFromTestCase(
            #TestMockIntraAnalysisSomaWorkflowRunner)
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
            TestMockIntraAnalysisBvParamTemplateSomaWorkflowRunner))
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([
            #TestMockIntraAnalysisSomaWorkflowRunner(options.test),
            TestMockIntraAnalysisBvParamTemplateSomaWorkflowRunner(
                options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
