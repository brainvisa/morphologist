from morphologist.study import Study
from morphologist.tests.mocks.analysis import MockAnalysis

class MockStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockAnalysis()
   
    @staticmethod
    def _analysis_cls():
        return MockAnalysis


