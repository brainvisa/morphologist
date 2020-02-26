from __future__ import absolute_import
import unittest

from morphologist.core.tests.test_study import TestStudy
from morphologist.core.tests.test_subject import TestSubject
from morphologist.core.tests.test_analysis import TestAnalysis

from morphologist.tests.intra_analysis.test_analysis import TestIntraAnalysis
from morphologist.tests.intra_analysis.test_study import TestBrainvisaTemplateStudy, TestDefaultTemplateStudy


if __name__=='__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudy)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSubject))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestAnalysis))

    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestBrainvisaTemplateStudy))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDefaultTemplateStudy))

    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysis))

    # XXX: commented because ThreadRunner does not work anymore
    # suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestThreadRunner))

    unittest.TextTestRunner(verbosity=2).run(suite)


