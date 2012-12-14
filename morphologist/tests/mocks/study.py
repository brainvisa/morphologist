from morphologist.study import Study
from morphologist.tests.mocks.intra_analysis import MockIntraAnalysis
from morphologist.tests.mocks.analysis import MockAnalysis

class MockIntraAnalysisStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockIntraAnalysis()

    @staticmethod
    def _analysis_cls():
        return MockIntraAnalysis


class MockStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockAnalysis()
   
    @staticmethod
    def _analysis_cls():
        return MockAnalysis


