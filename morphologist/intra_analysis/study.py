from morphologist.core.study import Study
from morphologist.intra_analysis import IntraAnalysis


class IntraAnalysisStudy(Study):

    @staticmethod
    def _create_analysis():
        return IntraAnalysis()

    @staticmethod
    def analysis_cls():
        return IntraAnalysis

