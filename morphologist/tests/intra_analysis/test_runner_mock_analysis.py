import sys
import optparse
import unittest

from morphologist.tests.test_runner import TestRunnerSomaWorkflow
from morphologist.tests.intra_analysis.study import MockIntraAnalysisStudyTestCase, MockIntraAnalysisStudyTestCaseBvParamTemplate


class TestRunnerMockIntraAnalysisSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCase() 


class TestRunnerMockIntraAnalysisBvParamTemplateSomaWorkflow(TestRunnerSomaWorkflow):

    def create_test_case(self):
        return MockIntraAnalysisStudyTestCaseBvParamTemplate()


if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test',
                      dest="test", default=None,
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisSomaWorkflow)
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRunnerMockIntraAnalysisBvParamTemplateSomaWorkflow))
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([TestRunnerMockIntraAnalysisSomaWorkflow(options.test), TestRunnerMockIntraAnalysisBvParamTemplateSomaWorkflow(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
