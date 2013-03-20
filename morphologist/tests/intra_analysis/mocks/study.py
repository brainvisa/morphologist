from morphologist.core.study import Study
from morphologist.tests.intra_analysis.mocks.analysis import MockIntraAnalysis


class MockIntraAnalysisStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockIntraAnalysis()

    @staticmethod
    def analysis_cls():
        return MockIntraAnalysis




