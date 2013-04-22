from morphologist.core.study import Study
from morphologist.core.analysis import AnalysisFactory


class MockStudy(Study):

    def __init__(self, *args, **kwargs):
        super(MockStudy, self).__init__(*args, **kwargs)

    @staticmethod
    def _mockified_analysis_type(analysis_type):
        return 'Mock' + analysis_type
        
    def analysis_cls(self):
        mock_analysis_type = self._mockified_analysis_type(self.analysis_type)
        return AnalysisFactory.get_analysis_cls(mock_analysis_type)
    
    def _create_analysis(self):
        mock_analysis_type = self._mockified_analysis_type(self.analysis_type)
        return AnalysisFactory.create_analysis(mock_analysis_type,
                                            self.parameter_template)
 
    @classmethod
    def from_organized_directory(cls, analysis_type, organized_directory,
                                                parameter_template_name):
        mock_analysis_type = self._mockified_analysis_type(self.analysis_type)
        Study.from_organized_directory(mock_analysis_type, organized_directory,
                                                parameter_template_name)
