from morphologist.core.study import Study
from morphologist.core.tests.mocks.analysis import MockAnalysis


class MockStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockAnalysis()
   
    @staticmethod
    def analysis_cls():
        return MockAnalysis


