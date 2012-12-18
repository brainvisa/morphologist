from morphologist.study import Study
from morphologist.intra_analysis import IntraAnalysis

class IntraAnalysisStudy(Study):

    @staticmethod
    def _create_analysis():
        return IntraAnalysis()

    @staticmethod
    def _analysis_cls():
        return IntraAnalysis

