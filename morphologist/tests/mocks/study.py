from morphologist.study import Study
from morphologist.tests.mocks.intra_analysis import MockIntraAnalysis

class MockStudy(Study):

    @staticmethod
    def _create_analysis():
        return MockIntraAnalysis()


