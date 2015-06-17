from morphologist.core.study import Study


class IntraAnalysisStudy(Study):

    def __init__(self, name="undefined study", 
                 output_directory=Study.default_output_directory):
        super(IntraAnalysisStudy, self).__init__(
            analysis_type="IntraAnalysis",
            name=name, output_directory=output_directory)

