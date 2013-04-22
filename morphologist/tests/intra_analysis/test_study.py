import unittest

from morphologist.core.tests.test_study import TestStudy
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCaseBvParamTemplate, \
                                                    IntraAnalysisStudyTestCase


class TestBrainvisaTemplateStudy(TestStudy):

    def create_test_case(self):
        test_case = IntraAnalysisStudyTestCaseBvParamTemplate()
        return test_case


class TestDefaultTemplateStudy(TestStudy):

    def create_test_case(self):
        test_case = IntraAnalysisStudyTestCase()
        return test_case 


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrainvisaTemplateStudy)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDefaultTemplateStudy))
    unittest.TextTestRunner(verbosity=2).run(suite)
