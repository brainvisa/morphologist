import unittest

from morphologist.analysis import MockAnalysis


def create_analysis():
    analysis = MockAnalysis()
    return analysis

class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.analysis = create_analysis()

    def test_run_analysis(self):
        self.analysis.run()
        self.assert_(self.analysis.is_running()) 


    def _test_stop_analysis(self):
        self.analysis.run()
        self.analysis.stop()
        self.assert_(not self.analysis.is_running())

    def tearDown(self):
        if self.analysis.is_running():
            self.analysis.stop()

if __name__ == '__main__':
    
    unittest.main()
